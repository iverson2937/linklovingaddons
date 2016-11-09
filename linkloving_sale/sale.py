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


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    tax_id = fields.Many2many(related='order_id.tax_id', store=True)
