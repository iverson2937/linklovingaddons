# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockMoveFinished(models.Model):
    """
    计算产成品model
    """
    _name = 'stock.move.finished'
    product_id = fields.Many2one('product.product', )
    production_id = fields.Many2one('mrp.production')
    suggest_qty = fields.Float(string=u'待生产')

    product_type = fields.Selection(string="物料类型", selection=[('semi-finished', '流转品'),
                                                              ('material', '原材料'),
                                                              ('real_semi_finished', '半成品')],
                                    required=False, compute="_compute_product_type")

    @api.multi
    def _compute_product_type(self):
        circulate_location = self.env["stock.location"].search([("is_circulate_location", "=", True)], limit=1)
        semi_finished_location = self.env["stock.location"].search([("is_semi_finished_location", "=", True)], limit=1)
        fixed_location_ids = self.env["stock.fixed.putaway.strat"]
        semi_finished_fixed_location_ids = self.env["stock.fixed.putaway.strat"]
        if circulate_location and circulate_location.putaway_strategy_id and circulate_location.putaway_strategy_id.fixed_location_ids:
            fixed_location_ids = circulate_location.putaway_strategy_id.fixed_location_ids
        if semi_finished_location and semi_finished_location.putaway_strategy_id and semi_finished_location.putaway_strategy_id.fixed_location_ids:
            semi_finished_fixed_location_ids = semi_finished_location.putaway_strategy_id.fixed_location_ids
        for sim in self:
            if sim.product_id.categ_id.id in fixed_location_ids.mapped("category_id").ids:
                sim.product_type = "semi-finished"  # 半成品流转
            elif sim.product_id.categ_id.id in semi_finished_fixed_location_ids.mapped("category_id").ids:
                sim.product_type = "real_semi_finished"  # 半成品
            else:
                sim.product_type = "material"

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
            quantity_done_finished = 0
            stock_moves = sim_move.production_id.move_finished_ids.filtered(
                lambda x: x.product_id.id == sim_move.product_id.id)
            for move in stock_moves:
                if move.state == 'done':
                    quantity_done_finished = quantity_done_finished + move.quantity_done
                else:

                    if move.qc_feedback_lines:
                        if move.qc_feedback_lines[0].feedback_id.state not in ['qc_fail', 'check_to_rework']:

                            quantity_done_finished = quantity_done_finished + move.quantity_done
                        else:
                            if sim_move.production_id.state in ['progress'] and not sim_move.production_id.feedback_on_rework :
                                quantity_done_finished = quantity_done_finished + move.quantity_done

                            # if sim_move.production_id.state =='progress' and sim_move.production_id.feedback_on_rework:
                            #     pass


            sim_move.quantity_done_finished = quantity_done_finished

    quantity_done_finished = fields.Float(default=0, compute=_compute_quantity_done_finished)
    produce_qty = fields.Float()
