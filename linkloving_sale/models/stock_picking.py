# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, SUPERUSER_ID
from itertools import groupby

from odoo.tools import float_compare


class StockPicking(models.Model):
    """

    """""

    _inherit = 'stock.picking'
    is_emergency = fields.Boolean(string=u'加急')



