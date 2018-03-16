# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_total_o = fields.Monetary(string=u'Invoice Amount',
                                     store=True, readonly=True, track_visibility='always')
    commission = fields.Float(string=u'折算提成金额', track_visibility='onchange')

    @api.multi
    def parse_invoice_line_data(self):

        for invoice in self:
            data = []
            for line in invoice.invoice_line_ids:
                if line.invoice_line_tax_ids:

                    tax_name = line.invoice_line_tax_ids[0].amount / 100
                    untax_price_unit = line.price_unit / (1 + float(tax_name))
                    tax_type = line.invoice_line_tax_ids[0].type_tax_use
                else:
                    tax_name = 0
                    untax_price_unit = line.price_unit
                    tax_type = 'bank'

                res = {
                    'product_name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.name,
                    'quantity': line.quantity,
                    # 未税单价
                    'untax_price_unit': untax_price_unit,
                    # 单价
                    'price_unit': line.price_unit,
                    # 未税金额
                    'price_subtotal': line.price_subtotal,
                    # 含稅金額
                    'subtotal': line.quantity * line.price_unit,
                    'tax_name': 0.17,

                    'tax_type': tax_type
                }
                data.append(res)
            return data

    @api.multi
    def _get_po_number(self):
        for invoice in self:
            if invoice.origin:
                po = invoice.env['purchase.order'].search([('name', '=', invoice.origin)])
                invoice.po_id = po.id if po else None

    po_id = fields.Many2one('purchase.order', compute=_get_po_number)

    @api.multi
    def _get_so_number(self):
        for invoice in self:
            if invoice.origin:
                so = invoice.env['sale.order'].sudo().search([('name', '=', invoice.origin)])
                invoice.so_id = so.id if so else None

    so_id = fields.Many2one('sale.order', compute=_get_so_number)
    order_line = fields.One2many('purchase.order.line', related='po_id.order_line')
    deduct_amount = fields.Float(string=u'扣款')
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
        ('validate', u'验证'),
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

    # @api.multi
    # def write(self, vals):
    #     for invoice in self:
    #         if not invoice.amount_total_o:
    #             amount_total_o = 0
    #             for line in invoice.invoice_line_ids:
    #                 line.price_unit_o = line.price_unit
    #                 amount_total_o += line.price_unit_o * line.quantity
    #             vals.update({'amount_total_o': amount_total_o})
    #         if 'deduct_amount' in vals:
    #             deduct_amount = vals['deduct_amount']
    #             if deduct_amount > (invoice.amount_total_o or vals.get('amount_total_o')):
    #                 raise UserError(_('Deduct Amount can not larger than Invoice Amount'))
    #             if invoice.amount_total_o or vals.get('amount_total_o'):
    #                 rate = deduct_amount / (invoice.amount_total_o or vals.get('amount_total_o'))
    #                 for line in invoice.invoice_line_ids:
    #                     if line.price_unit_o:
    #                         line.price_unit = line.price_unit_o * (1 - rate)
    #                     else:
    #                         line.price_unit = line.price_unit * (1 - rate)
    #     return super(AccountInvoice, self).write(vals)

    @api.multi
    def action_reject(self):
        self.state = 'draft'

    def parse_invoice_data(self):

        return {
            'name': self.number,
            'partner_name': self.partner_id.name,
            'line_ids': [
                {
                    'product_name': line.product_id.name,
                    'short_name': line.product_id.name.split('-')[0],
                    'qty': line.quantity,
                    'price_unit': line.price_unit,
                    'total_amount': line.quantity * line.price_unit
                }
                for line in self.invoice_line_ids
            ]
        }

    @api.multi
    def button_reset_taxes(self):
        for invoice in self:
            self._cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (invoice.id,))
            self.invalidate_cache()
            self.compute_taxes()

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

    price_unit_o = fields.Float(digits=dp.get_precision('Product Price'), string=u'原始单价')
    price_subtotal_o = fields.Monetary()
    # price_subtotal_o = fields.Monetary(string='Amount',
    #                                    store=True, readonly=True, compute='_compute_price')
    # price_unit = fields.Float(digits=dp.get_precision('Price Deduct'), string=u'单价')
    #
    # # 添加原始总价在invoice_line
    # @api.one
    # @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
    #              'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    # def _compute_price(self):
    #     currency = self.invoice_id and self.invoice_id.currency_id or None
    #     price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
    #     taxes = False
    #     if self.invoice_line_tax_ids:
    #         taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
    #                                                       partner=self.invoice_id.partner_id)
    #     self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
    #     self.price_subtotal_o = self.quantity * self.price_unit_o
    #     if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
    #         price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed,
    #                                                                     self.invoice_id.company_id.currency_id)
    #     sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
    #     self.price_subtotal_signed = price_subtotal_signed * sign
    #
    # @api.model
    # def create(self, vals):
    #     """
    #     原始单价存起来
    #     :param vals:
    #     :return:
    #     """
    #     res = super(AccountInvoiceLine, self).create(vals)
    #     res.price_unit_o = res.price_unit
    #     return res
