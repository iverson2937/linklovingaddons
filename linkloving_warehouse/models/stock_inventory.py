# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


class StockInventory(models.Model):
    _inherit = 'stock.inventory'
    remark = fields.Char(string=u'备注')
