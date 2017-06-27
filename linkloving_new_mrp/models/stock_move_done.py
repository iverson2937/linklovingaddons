# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockMoveFinished(models.Model):
    _name = 'stock.move.finished'
    product_id = fields.Many2one('product.product', )
    production_id = fields.Many2one('mrp.production')

    def _compute_stock_moves_finished(self):
        for sim_move in self:
            sim_move.stock_moves = []
            for move in sim_move.production_id.move_finished_ids:
                if move.product_id == sim_move.product_id:
                    sim_move.stock_moves_finished = sim_move.stock_moves + move

    stock_moves_finished = fields.One2many('stock.move', compute=_compute_stock_moves_finished)

    def _compute_raw_material_production_id(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.procurement_id = sim_move.stock_moves[0].procurement_id

    raw_material_production_id = fields.Many2one('mrp.production', compute=_compute_raw_material_production_id)

    def _compute_quantity_done_finished(self):

        for sim_move in self:
            print sim_move
            # move_to_fill = self.env['stock.move'].search([('production_id', '=', sim_move.production_id.id)])
            sim_move.quantity_done = 0
            for move in sim_move.production_id.move_finished_ids:
                if move.product_id == sim_move.product_id and not move.is_return_material and move.state == "done":
                    sim_move.quantity_done_finished += move.quantity_done

    quantity_done_finished = fields.Float(default=0, compute=_compute_quantity_done_finished)
    quantity_done = fields.Float(default=0, compute=_compute_quantity_done_finished)
