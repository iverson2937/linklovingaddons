# -*- coding: utf-8 -*-
from email import utils

from odoo import models, fields, api, _
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    req_line_id = fields.Many2one('purchase.request.line')
