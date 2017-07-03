# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductSpecs(models.Model):
    _name = 'product.specs'

    name = fields.Char(string=u'代码')
    categ_id = fields.Many2one('product.category')
