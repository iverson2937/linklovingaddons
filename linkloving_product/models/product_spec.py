# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductSpecs(models.Model):
    _name = 'product.spec'

    name = fields.Char(string=u'名称')
    code = fields.Char(string=u'代码')
    remark = fields.Char()
    categ_id = fields.Many2one('product.category')
    is_sub = fields.Boolean(default=False)
