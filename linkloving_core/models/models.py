# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_detail(self):
        product_id = self.env['product.template'].browse(45964);
        return {
            'name': product_id.name,
            'bom_lines': [
                {'name': 'product2'},
                {'name': 'product'},
                {'name': 'product3'}
            ]
        }
