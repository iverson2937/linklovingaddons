# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    """
    产品分类
    """
    _inherit = 'product.template'
    brand_id = fields.Many2one('product.category.brand', related='categ_id.brand_id')
    area_id = fields.Many2one('product.category.area', related='categ_id.area_id')
