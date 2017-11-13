# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'ir.needaction_mixin', 'mail.thread']
    team_id = fields.Many2one('crm.team', related='partner_id.team_id')
    customer = fields.Boolean(related='partner_id.customer')
    partner_id = fields.Many2one('res.partner', track_visibility='onchange')
    state = fields.Selection(selection_add=[('confirm', u'销售确认'), ('cancel', u'取消'), ('done', u'完成')],
                             track_visibility='onchange')
    remark = fields.Text(string='备注')
    product_id = fields.Many2one('product.product')

    balance_amount = fields.Float(string=u'余额', compute='_get_balance_amount')

    @api.multi
    def _get_balance_amount(self):
        for payment in self:
            if payment.partner_id:
                sum()
                for move in payment.move_line_ids:
                    pass

    # origin = fields.Char(string=u'源单据')
    @api.multi
    def set_to_post(self):
        self.state = 'posted'

    @api.multi
    def set_to_cancel(self):
        account_invoices = self.env['account.invoice'].search([('type', '=', 'out_invoice'), ('state', '=', 'open')],
                                                              limit=300)
        for invoice in account_invoices:
            invoice.auto_set_to_done()

            # account_invoices = self.env['account.invoice'].search([('type', '=', 'in_invoice')], limit=400, offset=2500)
            # print len(account_invoices)
            # for invoice in account_invoices:
            #     if invoice.partner_id.supplier:
            #         print invoice.name
            #         invoice.journal_id = 2
            # payment_ids = self.env['account.payment'].search([('payment_type', '=', 'inbound')])
            # ids = []
            # for payment in payment_ids:
            #     if payment.partner_id:
            #         for move in payment.move_line_ids:
            #             if not move.partner_id:
            #                 ids.append(payment.id)
            #                 move.partner_id = payment.partner_id.id
            #




            # # FIXME: 怎么样的可以取消
            # if self.move_line_ids and len(self.move_line_ids) == 2 and self.payment_type != 'transfer':
            #     raise UserError('不可以取消,请联系系统管理员')
            # else:
            #     self.state = 'cancel'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if len(self.move_line_ids) > 2:
            raise UserError(u'不允许修改')
        if self.product_id and not self.product_id.property_account_income_id:
            raise UserError(u'请设置产品收入科目')
        if self.move_line_ids:
            for move in self.move_line_ids:
                if move.move_id.state == 'posted':
                    raise UserError(u'不可修改已过账的分录')
                if move.account_id != self.journal_id.default_credit_account_id:
                    move.account_id = self.product_id.property_account_income_id.id

    def set_to_done(self):
        if self.partner_type == 'customer' and not self.partner_id:
            raise UserError(u'请填写客户')
        if self.partner_id:
            for move in self.move_line_ids:
                move.partner_id = self.partner_id
        self.state = 'done'

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        # Set partner_id domain
        if self.partner_type == 'employee':
            return {'domain': {'partner_id': [(self.partner_type, '=', True)]}}
        elif self.partner_type in ('customer', 'supplier'):
            return {'domain': {'partner_id': [(self.partner_type, '=', True), ('is_company', '=', True)]}}

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            amount = 0.0
            for balance_id in invoice['balance_ids']:
                balance_obj = self.env['account.payment.register.balance']
                balance = balance_obj.browse(balance_id)
                if not balance.state:
                    amount += balance.amount
            rec['communication'] = invoice['reference'] or invoice['name'] or invoice['number']
            rec['currency_id'] = invoice['currency_id'][0]
            rec['payment_type'] = invoice['type'] in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
            rec['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[invoice['type']]
            rec['partner_id'] = invoice['partner_id'][0]
            rec['amount'] = amount
        return rec

    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state not in ['draft', 'approve']:
                raise UserError(
                    _("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            sequence_code = 'account.payment.employee'
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'

            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                elif rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
                elif rec.partner_type == 'other':
                    sequence_code = 'account.payment.other'
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                sequence_code)

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()
            # add by allen
            for balance in rec.invoice_ids.balance_ids:
                balance.state = 1
            state = 'posted'
            if self.partner_type == 'customer' and self.payment_type == 'inbound':
                state = 'confirm'
            rec.write({'state': state, 'move_name': move.name})

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        state = self._context.get('state')
        return [('state', '=', state)]

    def _get_counterpart_move_line_vals(self, invoice=False):
        if self.payment_type == 'transfer':
            name = self.name
        elif self.payment_type == 'other':
            name = u'其他收入'
        else:
            name = ''
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    name += _("Customer Payment")
                elif self.payment_type == 'outbound':
                    name += _("Customer Refund")
            elif self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    name += _("Vendor Refund")
                elif self.payment_type == 'outbound':
                    name += _("Vendor Payment")
            if invoice:
                name += ': '
                for inv in invoice:
                    if inv.move_id:
                        name += inv.number + ', '
                name = name[:len(name) - 2]

        return {
            'name': name,
            'account_id': self.destination_account_id.id if self.destination_account_id else self.product_id.property_account_income_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
            'payment_id': self.id,
        }

    @api.multi
    def button_journal_entries(self):

        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_ids.ids)],
        }
