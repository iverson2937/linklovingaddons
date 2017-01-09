# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, SUPERUSER_ID


class SaleOrder(models.Model):
    """

    """""

    _inherit = 'sale.order'
    tax_id = fields.Many2one('account.tax', required=True)
    product_count = fields.Float(compute='get_product_count')
    pi_number = fields.Char(string='PI Number')

    def get_product_count(self):
        count = 0.0
        for line in self.order_line:
            count += line.product_uom_qty
        self.product_count = count




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_specs = fields.Text(string=u'产品规格', related='product_id.product_specs')

