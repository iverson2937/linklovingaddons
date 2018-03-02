# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def view_new_product_cost(self):
        return {
            "type": "ir.actions.client",
            "tag": "cost_detail_new",
            'product_id': self.id,
        }

    @api.multi
    def get_product_cost_new(self):
        res = []

        return res
