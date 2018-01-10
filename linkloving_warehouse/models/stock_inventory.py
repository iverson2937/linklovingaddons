# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


class StockInventoryInherit(models.Model):
    _inherit = 'stock.inventory'
    remark = fields.Selection([
        ('transfer', '物料转换'),
        ('adjust', '库存调整')
    ], string=u'来源备注', default='adjust')
