# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductCategory(models.Model):
    """
    产品分类
    """
    _inherit = 'product.category'
    brand_id = fields.Many2one('product.category.brand')
    area_id = fields.Many2one('product.category.area')
