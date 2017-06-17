# -*- coding: utf-8 -*-
import math

import datetime
from odoo import models, fields, api, _
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError


class NewMrpProduction(models.Model):
    _inherit = 'mrp.production'
    is_multi_output = fields.Boolean(default=True)
    output_product_ids = fields.One2many('mrp.production.material', 'mo_id', domain=[('type', '=', 'output')])
    input_product_ids = fields.One2many('mrp.production.material', 'mo_id', domain=[('type', '=', 'input')])

    @api.multi
    def confirm_output(self):
        for line in self.output_product_ids:
            for finish_id in self.move_finished_ids:
                if line.product_id.id == finish_id.product_id.id:
                    finish_id.product_uom_qty = line.produce_qty

        @api.multi
        def do_produce(self):
            # Nothing to do for lots since values are created using default data (stock.move.lots)
            moves = self.production_id.move_raw_ids
            quantity = self.product_qty
            if float_compare(quantity, 0, precision_rounding=self.product_uom_id.rounding) <= 0:
                raise UserError(_('You should at least produce some quantity'))
            for move in moves.filtered(lambda x: x.product_id.tracking == 'none' and x.state not in ('done', 'cancel')):
                if move.unit_factor:
                    rounding = move.product_uom.rounding
                    move.quantity_done_store += float_round(quantity * move.unit_factor, precision_rounding=rounding)
            moves = self.production_id.move_finished_ids.filtered(
                lambda x: x.product_id.tracking == 'none' and x.state not in ('done', 'cancel'))
            for move in moves:
                rounding = move.product_uom.rounding
                if move.product_id.id == self.production_id.product_id.id:
                    move.quantity_done_store += float_round(quantity, precision_rounding=rounding)
                elif move.unit_factor:
                    # byproducts handling
                    move.quantity_done_store += float_round(quantity * move.unit_factor, precision_rounding=rounding)
            self.check_finished_move_lots()
            if self.production_id.state == 'confirmed':
                self.production_id.write({
                    'state': 'progress',
                    'date_start': datetime.now(),
                })
            return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def button_multi_output(self):
        view = self.env.ref('linkloving_new_mrp.output_material_form')
        return {'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': self.id,
                # 'context': {'picking_mode': picking_mode,
                #             'overpicking_invisible': overpicking_invisible,
                #             'quantity_ready_invisible': quantity_ready_invisible},
                'target': 'new'}

    @api.multi
    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            produced = sum(production.move_finished_ids.mapped('quantity_done'))
            if wizard.product_qty < produced:
                raise UserError(
                    _("You have already processed %d. Please input a quantity higher than %d ") % (produced, produced))
            production.write({'product_qty': wizard.product_qty})
            done_moves = production.move_finished_ids.filtered(
                lambda x: x.state == 'done' and x.product_id == production.product_id)
            qty_produced = production.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')),
                                                                          production.product_uom_id)
            factor = production.product_uom_id._compute_quantity(production.product_qty - qty_produced,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor,
                                                    picking_type=production.bom_id.picking_type_id)
            if production.is_rework or production.is_multi_output:
                for line in production.rework_material_line_ids:
                    production.update_rework_material(line, production.product_qty)

            else:
                for line, line_data in lines:
                    production._update_raw_move(line, line_data)
            operation_bom_qty = {}
            for bom, bom_data in boms:
                for operation in bom.routing_id.operation_ids:
                    operation_bom_qty[operation.id] = bom_data['qty']
            self._update_product_to_produce(production, production.product_qty - qty_produced)
            moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            moves.do_unreserve()
            moves.action_assign()
            for wo in production.workorder_ids:
                operation = wo.operation_id
                if operation_bom_qty.get(operation.id):
                    cycle_number = math.ceil(
                        operation_bom_qty[operation.id] / operation.workcenter_id.capacity)  # TODO: float_round UP
                    wo.duration_expected = (operation.workcenter_id.time_start +
                                            operation.workcenter_id.time_stop +
                                            cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
                if production.product_id.tracking == 'serial':
                    quantity = 1.0
                else:
                    quantity = wo.qty_production - wo.qty_produced
                    quantity = quantity if (quantity > 0) else 0
                wo.qty_producing = quantity
                if wo.qty_produced < wo.qty_production and wo.state == 'done':
                    wo.state = 'progress'
                # assign moves; last operation receive all unassigned moves
                # TODO: following could be put in a function as it is similar as code in _workorders_create
                # TODO: only needed when creating new moves
                moves_raw = production.move_raw_ids.filtered(
                    lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
                if wo == production.workorder_ids[-1]:
                    moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
                moves_finished = production.move_finished_ids.filtered(
                    lambda move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
                moves_raw.mapped('move_lot_ids').write({'workorder_id': wo.id})
                (moves_finished + moves_raw).write({'workorder_id': wo.id})
                if wo.move_raw_ids.filtered(lambda x: x.product_id.tracking != 'none') and not wo.active_move_lot_ids:
                    wo._generate_lot_ids()
        return {}

        # @api.multi
        # def change_prod_qty(self):
        #     # self.mo_id.write({'state': 'waiting_material'})
        #     return super(ChangeProductionQty, self).change_prod_qty()

    def _generate_finished_moves(self):
        if self.is_multi_output:
            if not self.output_product_ids:
                raise UserError(u'请添加产出物料')
            for line in self.output_product_ids:
                move = self.env['stock.move'].create({
                    'name': self.name,
                    'date': self.date_planned_start,
                    'date_expected': self.date_planned_start,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uom_qty': self.product_qty,
                    'location_id': self.product_id.property_stock_production.id,
                    'location_dest_id': self.location_dest_id.id,
                    'move_dest_id': self.procurement_ids and self.procurement_ids[0].move_dest_id.id or False,
                    'procurement_id': self.procurement_ids and self.procurement_ids[0].id or False,
                    'company_id': self.company_id.id,
                    'production_id': self.id,
                    'origin': self.name,
                    'group_id': self.procurement_group_id.id,
                })
                move.action_confirm()
        else:
            move = self.env['stock.move'].create({
                'name': self.name,
                'date': self.date_planned_start,
                'date_expected': self.date_planned_start,
                'product_id': self.product_id.id,
                'product_uom': self.product_uom_id.id,
                'product_uom_qty': self.product_qty,
                'location_id': self.product_id.property_stock_production.id,
                'location_dest_id': self.location_dest_id.id,
                'move_dest_id': self.procurement_ids and self.procurement_ids[0].move_dest_id.id or False,
                'procurement_id': self.procurement_ids and self.procurement_ids[0].id or False,
                'company_id': self.company_id.id,
                'production_id': self.id,
                'origin': self.name,
                'group_id': self.procurement_group_id.id,
            })
            move.action_confirm()
            return move

    def _generate_raw_moves(self, exploded_lines):
        self.ensure_one()
        moves = self.env['stock.move']
        source_location = self.picking_type_id.default_location_src_id
        if self.is_multi_output:
            if not self.input_product_ids:
                raise UserError('请添加投入物料')
            for line_id in self.input_product_ids:
                data = {
                    'name': self.name,
                    'date': self.date_planned_start,
                    'product_id': line_id.product_id.id,
                    'product_uom_qty': self.product_qty,
                    'product_uom': line_id.product_id.uom_id.id,
                    'location_id': source_location.id,
                    'location_dest_id': line_id.product_id.property_stock_production.id,
                    'raw_material_production_id': self.id,
                    'company_id': self.company_id.id,
                    'price_unit': line_id.product_id.standard_price,
                    'procure_method': 'make_to_stock',
                    'origin': self.name,
                    'warehouse_id': source_location.get_warehouse().id,
                    'group_id': self.procurement_group_id.id,
                    'propagate': self.propagate,
                    'suggest_qty': self.product_qty,
                }
                moves.create(data)



        else:
            for bom_line, line_data in exploded_lines:
                moves += self._generate_raw_move(bom_line, line_data)
        return moves


class MrpProductionMaterial(models.Model):
    _name = 'mrp.production.material'
    product_id = fields.Many2one('product.product', string=u'产品', required=True)
    total_produce_qty = fields.Float(string=u'累计产出数量')
    produce_qty = fields.Float(string=u'产出数量')

    mo_id = fields.Many2one('mrp.production')
    type = fields.Selection([
        ('input', '输入'),
        ('output', '输出')
    ])
