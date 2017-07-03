# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductCategory(models.Model):
    _name = 'product.sub.category'

    code = fields.Char(string=u'代码')
    categ_id = fields.Many2one('product.category')
