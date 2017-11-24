# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    by_order=fields.Boolean(compute='get_is_by_order')
    @api.multi
    def get_is_by_order(self):
        for order in self:
            order_lines= order.mapped('order_line')
            product_ids=[]
            for line in order_lines:
                product_ids.append(line.product_id)
            print product_ids
            if any(product.order_ll_type=='ordering' for product in product_ids):
                order.by_order=True
                print 'ddddddddddddddddddddddddddddd'
            else:
                order.by_order=False
                print 'ffffffffffffffffffffffffffffffffffffffffff'

