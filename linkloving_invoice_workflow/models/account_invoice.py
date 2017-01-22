# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_total_o = fields.Monetary(string=u'对账金额',
                                     store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    def _get_po_number(self):
        if self.origin:
            po = self.env['purchase.order'].search([('name', '=', self.origin)])
            self.po_id = po.id if po else None

    po_id = fields.Many2one('purchase.order', compute=_get_po_number)
    order_line = fields.One2many('purchase.order.line', related='po_id.order_line')
    deduct_amount = fields.Float(string=u'对账扣款')
    deduct_rate = fields.Float()
    remark = fields.Text(string=u'备注')

    # def _check_deduct_amount(self):
    #     for invoice in self:
    #         if invoice.deduct_amount > invoice.amount_total:
    #             return False
    #     return True

    # _constraints = [
    #     (_check_deduct_amount, u'扣款金额不能大于对账单金额', []),
    # ]

    state = fields.Selection([
        ('draft', 'Draft'),
        ('post', u'提交'),
        ('validate', u'确认'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' status is used when the invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    @api.multi
    def action_post(self):
        self.state = 'validate'

    @api.multi
    def action_reject(self):
        self.state = 'draft'

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft', 'validate']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('invoice_id.deduct_amount','invoice_id.amount_total_o')
    def _get_price_unit_actual(self):

        print '111111111111111', self.invoice_id.amount_total_o
        if self.invoice_id.amount_total_o:
            self.price_unit_actual = self.price_unit * \
                                     (1 - self.invoice_id.deduct_amount / self.invoice_id.amount_total_o)
        print '2222222222222222222',self.invoice_id.amount_total_o,self.price_unit_actual

    price_unit_actual = fields.Float(compute=_get_price_unit_actual, digits=dp.get_precision('Price Deduct'))
    price_subtotal_o = fields.Monetary(string='Amount',
                                       store=True, readonly=True, compute='_compute_price')

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity', 'invoice_id.deduct_amount',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None

        price = self.price_unit_actual * (1 - (self.discount or 0.0) / 100.0)
        print self.price_unit_actual, 'ddddddddddddddddddddddddddddddddddd'
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        self.price_subtotal_o = self.quantity * self.price_unit
        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed,
                                                                        self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
