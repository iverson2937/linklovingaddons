# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_receivable_amount(self):
        for res in self:
            orders = res.sale_order_ids.filtered(lambda x: x.invoice_status == 'to invoice')
            res.receivable_amount = sum(order.shipped_amount for order in orders)
            res.receivable_amount_real = res.credit + res.receivable_amount

    def _compute_payable_amount(self):
        for res in self:
            orders = self.env['purchase.order'].search(
                [('partner_id', '=', res.id), ('invoice_status', '=', 'to invoice')])
            res.payable_amount = sum(order.shipped_amount for order in orders) - sum(
                order.invoiced_amount for order in orders)
            res.payable_amount_real = res.debit + res.payable_amount

    receivable_amount = fields.Float(string=u'已出货未对账金额', compute=_compute_receivable_amount)
    payable_amount = fields.Float(string=u'已收货未付款金额', compute=_compute_payable_amount)
    payable_amount_real = fields.Float(string=u'总计', compute=_compute_payable_amount)
    receivable_amount_real = fields.Float(string=u'总计', compute=_compute_receivable_amount)
