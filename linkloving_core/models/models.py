# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def check_detail(self):
        print 'ssssssssssssss'
        {
            "type": "ir.actions.client",
            "tag": "petstore.homepage"
        }
