# -*- coding: utf-8 -*-

from odoo import models, fields, api


class NewMrpProduction(models.Model):
    _inherit = 'mrp.production'
    is_multi_output = fields.Boolean(default=True)
    output_product_ids = fields.Many2one('mrp.production.material', 'mo_id', domain=[('type', '=', 'output')])
    input_product_ids = fields.Many2one('mrp.production.material', 'mo_id', domain=[('type', '=', 'input')])


class MrpProductionMaterial(models.Model):
    _name = 'mrp.production.material'
    product_id = fields.Many2one('product.product', string=u'产品', required=True)
    mo_id = fields.Many2one('mrp.production')
    type = fields.Selection([
        ('input', '输入'),
        ('output', '输出')
    ])
