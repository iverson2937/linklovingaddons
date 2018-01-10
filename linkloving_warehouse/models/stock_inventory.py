# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


class StockInventoryInherit(models.Model):
    _inherit = 'stock.inventory'
    remark = fields.Char(string=u'备注')
