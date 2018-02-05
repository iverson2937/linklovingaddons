# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.expense'
    _order = 'create_date desc'

    department_id = fields.Many2one('hr.department', string=u'部门', related='sheet_id.department_id')
    doc = fields.Binary(attachment=True, string=u'附件')
    sale_id = fields.Many2one('sale.order')
    expense_no = fields.Char(related='sheet_id.expense_no')
    product_id = fields.Many2one('product.product', string='Product', readonly=True,
                                 states={'draft': [('readonly', False)], 'refused': [('readonly', False)],
                                         'done': [('readonly', False)]},
                                 domain=[('can_be_expensed', '=', True)], required=True)

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if expense.sheet_id.state == 'done':
                expense.state = "done"
            else:
                expense.state = "draft"

    # 产品变更不影响价格
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account

    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        重写 调整会计科目，低暂支的时候走其他应收科目
        '''
        for expense in self:
            journal = expense.sheet_id.bank_journal_id if expense.payment_mode == 'company_account' else expense.sheet_id.journal_id
            # create the move that will contain the accounting entries
            acc_date = expense.sheet_id.accounting_date or expense.date
            move = self.env['account.move'].create({
                'journal_id': journal.id,
                'company_id': self.env.user.company_id.id,
                'date': acc_date,
                'ref': expense.sheet_id.name,
                # force the name to the default value, to avoid an eventual 'default_name' in the context
                # to set it to '' which cause no number to be given to the account.move when posted.
                'name': '/',
            })
            company_currency = expense.company_id.currency_id
            diff_currency_p = expense.currency_id != company_currency
            # one account.move.line per expense (+taxes..)
            move_lines = expense._move_line_get()

            # create one more move line, a counterline for the total on payable account
            payment_id = False
            total, total_currency, move_lines = expense._compute_expense_totals(company_currency, move_lines, acc_date)
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (
                    expense.sheet_id.bank_journal_id.name))
                emp_account = expense.sheet_id.bank_journal_id.default_credit_account_id.id
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = (
                                  total < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': total < 0 and 'outbound' or 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'reconciled',
                    'currency_id': diff_currency_p and expense.currency_id.id or journal_currency.id,
                    'amount': diff_currency_p and abs(total_currency) or abs(total),
                    'name': expense.name,
                })
                payment_id = payment.id
            else:
                if not expense.employee_id.address_home_id:
                    raise UserError(_("No Home Address found for the employee %s, please configure one.") % (
                    expense.employee_id.name))
                emp_account = expense.employee_id.address_home_id.property_account_payable_id.id
                # 如果是用暂支抵扣的就用其他应收科目
                if expense.sheet_id.is_deduct_payment:
                    emp_account = expense.employee_id.address_home_id.property_account_receivable_id.id

            aml_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            move_lines.append({
                'type': 'dest',
                'name': aml_name,
                'price': total,
                'account_id': emp_account,
                'date_maturity': acc_date,
                'amount_currency': diff_currency_p and total_currency or False,
                'currency_id': diff_currency_p and expense.currency_id.id or False,
                'payment_id': payment_id,
            })

            # convert eml into an osv-valid format
            lines = map(lambda x: (0, 0, expense._prepare_move_line(x)), move_lines)
            move.with_context(dont_create_taxes=True).write({'line_ids': lines})
            expense.sheet_id.write({'account_move_id': move.id})
            move.post()
            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()
        return True
