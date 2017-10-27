# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    is_scrapy = fields.Boolean(default=False)
