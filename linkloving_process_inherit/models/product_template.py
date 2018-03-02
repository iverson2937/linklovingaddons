# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def view_new_product_cost(self):
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",

        }
