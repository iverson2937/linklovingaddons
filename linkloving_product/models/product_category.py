# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    code = fields.Char(string=u'代码')
