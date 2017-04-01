# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, SUPERUSER_ID
from itertools import groupby

from odoo.tools import float_compare


class StockPicking(models.Model):
    """

    """""

    _inherit = 'stock.picking'
    return_id = fields.Many2one('return.goods')


class StockMove(models.Model):
    _inherit = 'stock.move'
    return_line_id = fields.Many2one('return.goods.line')
