# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, SUPERUSER_ID
from itertools import groupby

from odoo.tools import float_compare


class StockPicking(models.Model):
    """

    """""

    _inherit = 'stock.picking'
    rma_id = fields.Many2one('return.goods')


class StockMove(models.Model):
    _inherit = 'stock.move'
    rma_line_id = fields.Many2one('return.goods.line')

    @api.multi
    def action_done(self):
        super(StockMove, self).action_done()
        for move in self:
            move.rma_line_id._get_qty_delivered()
