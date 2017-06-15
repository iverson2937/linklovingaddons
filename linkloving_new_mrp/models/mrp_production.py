# -*- coding: utf-8 -*-

from odoo import models, fields, api


class NewMrpProduction(models.Model):
    _inherit = 'mrp.production'
    is_multi_output = fields.Boolean(default=True)
    output_product_ids = fields.Many2many('product.product')

# class InputMaterialLine
