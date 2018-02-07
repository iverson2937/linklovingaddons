# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductCategoryBrand(models.Model):
    """
    品牌
    """
    _name = 'product.category.brand'
    name = fields.Char(string='名称')
    description = fields.Text(string='描述')


class ProductCategoryArea(models.Model):
    """
        区域

    """
    _name = 'product.category.area'
    name = fields.Char(string='名称')
    description = fields.Text(string='描述')
