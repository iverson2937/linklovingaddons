# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockMove(models.Model):
    """
    计算产成品model
    """
    _inherit = 'stock.move'

    qc_feedback_lines = fields.One2many('mrp.qc.feedback.line', 'finished_move_id')


class SimStockMove(models.Model):
    _inherit = 'sim.stock.move'

    demand_qty = fields.Float(string='需求数量')
