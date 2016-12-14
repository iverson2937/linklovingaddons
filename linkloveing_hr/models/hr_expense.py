# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    department_id = fields.Many2one('hr.department', string=u'部门')

    @api.depends('employee_id')
    def onchange_employee_id(self):
        self.department_id = self.employee_id.department_id

    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        print 'ssssssssssss'
        for expense in self:
            journal = expense.sheet_id.bank_journal_id if expense.payment_mode == 'company_account' else expense.sheet_id.journal_id
            #create the move that will contain the accounting entries
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
            #one account.move.line per expense (+taxes..)
            move_lines = expense._move_line_get()

            #create one more move line, a counterline for the total on payable account
            payment_id = False
            total, total_currency, move_lines = expense._compute_expense_totals(company_currency, move_lines, acc_date)
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                emp_account = expense.sheet_id.bank_journal_id.default_credit_account_id.id
                journal = expense.sheet_id.bank_journal_id
                #create payment
                payment_methods = (total < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
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
                    raise UserError(_("No Home Address found for the employee %s, please configure one.") % (expense.employee_id.name))
                if expense.employee_id.address_home_id.payment_balance<expense.sheet_id.total_amount:
                    emp_account = expense.employee_id.address_home_id.property_account_payable_id.id
                else:
                    emp_account = expense.employee_id.address_home_id.employee_payment_id.id

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

            #convert eml into an osv-valid format
            lines = map(lambda x: (0, 0, expense._prepare_move_line(x)), move_lines)
            move.write({'line_ids': lines})
            expense.sheet_id.write({'account_move_id': move.id})
            move.post()
            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()
        return True




class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    expense_no = fields.Char(string=u'报销编号')
    approve_ids = fields.Many2many('res.users')

    @api.one
    @api.depends('employee_id.user_id.partner_id.payment_balance')
    def _get_pre_payment_reminding_balance(self):

            self.pre_payment_reminding = self.employee_id.user_id.partner_id.payment_balance

    pre_payment_reminding = fields.Float(string=u'暂支余额', compute=_get_pre_payment_reminding_balance)

    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        res = self.mapped('expense_line_ids').action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and self.pre_payment_reminding >= self.total_amount:
            self.write({'state': 'done'})
        else:
            self.write({'state': 'post'})
        return res

    def _get_is_show(self):
        if self._context.get('uid') == self.to_approve_id.id:
            self.is_show = True
        else:
            self.is_show = False

    is_show = fields.Boolean(compute=_get_is_show)

    to_approve_id = fields.Many2one('res.users', readonly=True, track_visibility='onchange')

    state = fields.Selection([('submit', 'Submitted'),
                              ('manager1_approve', '一级审核'),
                              ('manager2_approve', '二级审核'),
                              ('manager3_approve', '总经理审核'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False,
                             default='submit', required=True,
                             help='Expense Report State')

    @api.multi
    def manager1_approve(self):
        # if self.employee_id == self.employee_id.department_id.manager_id:
        #     self.to_approve_id = self.employee_id.department_id.parent_id.manager_id.user_id.id
        # else:
        department = self.to_approve_id.employee_ids.department_id
        if department.allow_amount and self.total_amount < department.allow_amount:
            self.to_approve_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

        else:
            self.to_approve_id = department.parent_id.manager_id.user_id.id

            self.write({'state': 'manager1_approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.multi
    def manager2_approve(self):
        department = self.to_approve_id.employee_ids.department_id
        if department.allow_amount and self.total_amount < department.allow_amount:
            self.to_approve_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

        else:
            self.to_approve_id = department.parent_id.manager_id.user_id.id

            self.write({'state': 'manager2_approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.multi
    def manager3_approve(self):

        self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.model
    def create(self, vals):
        if vals.get('expense_no', 'New') == 'New':
            vals['expense_no'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet') or '/'
            print vals['expense_no']
        exp = super(HrExpenseSheet, self).create(vals)
        if exp.employee_id == exp.employee_id.department_id.manager_id:
            department = exp.to_approve_id.employee_ids.department_id
            if department.allow_amount and self.total_amount > department.allow_amount:
                exp.write({'state': 'approve'})
            else:
                exp.to_approve_id = exp.employee_id.department_id.parent_id.manager_id.user_id.id
        else:
            exp.to_approve_id = exp.employee_id.department_id.manager_id.user_id.id
        return exp

    @api.multi
    def write(self, vals):
        if vals.get('state') == 'cancel':
            self.to_approve_id = False
        return super(HrExpenseSheet, self).write(vals)

    @api.multi
    def reset_expense_sheets(self):
        if self.employee_id == self.employee_id.department_id.manager_id:
            department = self.to_approve_id.employee_ids.department_id
            if department.allow_amount and self.total_amount > department.allow_amount:
                self.write({'state': 'approve'})
            else:
                self.to_approve_id = self.employee_id.department_id.parent_id.manager_id.user_id.id
        else:
            self.to_approve_id = self.employee_id.department_id.manager_id.user_id.id

        return self.write({'state': 'submit'})

    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        res = self.mapped('expense_line_ids').action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and self.pre_payment_reminding < self.total_amount:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        return res


