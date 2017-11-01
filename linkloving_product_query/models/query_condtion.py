# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductQueryCondition(models.TransientModel):
    _name = 'product.query.condition'
    scale = fields.Selection([
        ('all', '所有产品')
    ], string=u'产品范围')
    sales_min = fields.Integer()
    sales_max = fields.Integer()
    start_time = fields.Datetime(string='开始时间')
    end_time = fields.Datetime(string='结束时间')
