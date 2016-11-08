# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, SUPERUSER_ID


class SaleOrder(models.Model):
    """

    """""

    _inherit = 'sale.order'
    tax_id = fields.Many2many('account.tax', required=True)
    product_count = fields.Float(compute='get_product_count')

    def get_product_count(self):
        count = 0.0
        for line in self.order_line:
            count += line.product_uom_qty
        self.product_count = count

# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
#     tax_id = fields.Many2many(related='order_id.tax_id', store=True)
#
#     def default_get(self, cr, uid, ids, context=None):
#         res = super(SaleOrderLine, self).default_get(cr, uid, ids, context=None)
#         if context:
#             context_keys = context.keys()
#             next_sequence = 1
#             if 'order_line' in context_keys:
#                 if len(context.get('order_line')) > 0:
#                     next_sequence = len(context.get('order_line')) + 1
#         res.update({'sequence': next_sequence,'tax_id':context.get('default_tax_id')})
#         return res
