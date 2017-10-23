# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    code = fields.Selection(selection_add=[
        ('retail', u'电商出货')
    ])
