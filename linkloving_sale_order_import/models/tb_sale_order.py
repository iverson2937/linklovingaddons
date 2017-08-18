# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TBSaleOrder(models.Model):
    _name = 'tb.sale.order'
    name = fields.Char(string=u'订单编号')
    partner_id = fields.Many2one('res.partner', string=u'来源')
    total_amount = fields.Float(string=u'订单金额')
    deal_date = fields.datetime(string=u'成交时间')
    state = fields.Selection([
        ('', ''),
        ('', ''),
        ('', ''),
    ])


class TBSaleOrderLine(models.Model):
    _name = 'tb.sale.order.line'
    order_id = fields.Many2one('tb.sale.order')
    product = fields.Char(string=u'产品')
    price_unit = fields.Float(string=u'采购价')
    product_qty = fields.Float(string=u'')
