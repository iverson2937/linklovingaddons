# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TBSaleOrder(models.Model):
    _inherit = 'eb.order'

    total_amount = fields.Float(string=u'订单金额')
    deal_date = fields.Datetime(string=u'成交日期')

    def create_eb_sale_order(self, vals):
        line_ids = []
        for line in vals.get('items'):
            product_id = self.env['product.product'].search([('default_code', '=', '98.0A4000.104')])
            line_id = self.env['eb.order.line'].create({
                'product': line.get('product'),
                'product_id': product_id.id,
                'price_unit': line.price_unit,
                'product_qty': line.product_qty,
            })
            line_ids.append(line_id)
        self.create({
            'name': vals.name,
            'partner_id': vals.get('partner_id'),
            'deal_date': vals.get('deal_date'),
            'total_amount': vals.total_amount,
            'eb_order_line_ids': line_ids,
        })


class TBSaleOrderLine(models.Model):
    _inherit = 'eb.order.line'
    product = fields.Char(string=u'产品')
    price_unit = fields.Float(string=u'采购价')
    product_qty = fields.Float(string=u'采购数量')
