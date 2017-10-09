# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_receivable_amount(self):
        for res in self:
            orders = res.sale_order_ids.filtered(lambda x: x.invoice_status == 'to invoice')
            res.receivable_amount = sum(order.shipped_amount for order in orders)
            res.receivable_amount_real = res.credit - res.receivable_amount


    receivable_amount = fields.Float(string=u'已出货未对账金额', compute=_compute_receivable_amount)
    receivable_amount_real = fields.Float(string=u'总计', compute=_compute_receivable_amount)
