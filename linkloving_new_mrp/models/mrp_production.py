# -*- coding: utf-8 -*-
import math

import datetime
from odoo import models, fields, api, _
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError


class NewMrpProduction(models.Model):
    _inherit = 'mrp.production'
    is_multi_output = fields.Boolean(related='process_id.is_multi_output')
    rule_id = fields.Many2one('mrp.product.rule')
    stock_move_lines_finished = fields.One2many('stock.move.finished', 'production_id')
    is_force_output = fields.Boolean(string=u'是否要求产出完整', default=True)

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])],
        readonly=True, required=False,
        states={'confirmed': [('readonly', False)]})
    output_product_ids = fields.One2many('mrp.product.rule.line', related='rule_id.output_product_ids')
    input_product_ids = fields.One2many('mrp.product.rule.line', related='rule_id.input_product_ids')

    @api.multi
    def _compute_done_stock_move_lines(self, new_pr):
        list = []
        for move in new_pr.move_finished_ids:
            list.append(move.product_id.id)
        a = set(list)  # 不重复的set集合
        res_list = []
        stock_move_lines_finished = self.env["stock.move.finished"].search([("production_id", "=", new_pr.id)])
        if not stock_move_lines_finished:
            for r in a:
                dict = self._prepare_stock_move_done_values(r)
                res = self.env['stock.move.finished'].create(dict)
                res_list.append(res.id)
                new_pr.stock_move_lines_finished = res_list
        else:
            new_pr.stock_move_lines_finished = stock_move_lines_finished
            # else:
            #     for r in a:
            #         if r.product_id not in self.sim_stock_move_lines.mapped('product_id'):
            #             dict = self._prepare_sim_stock_move_values(r)
            #             res = self.env['sim.stock.move'].create(dict)
            #             self.sim_stock_move_lines |= res
            # return

    def _prepare_stock_move_done_values(self, value):
        return {
            'product_id': value,
            'production_id': self.id
        }

    @api.onchange('rule_id')
    def _on_change_rule_id(self):
        self.bom_id = False

    def button_waiting_material(self):
        if self.is_multi_output:

            if not self.output_product_ids or not self.input_product_ids:
                raise UserError(u'请添加投入产出')
        self.write({'state': 'waiting_material'})

    @api.multi
    def confirm_output(self):

        for line in self.output_product_ids:
            for finish_id in self.move_finished_ids:
                if line.product_id.id == finish_id.product_id.id:
                    finish_id.quantity_done += line.produce_qty
                    line.produce_qty=0

        if sum(move.quantity_done for move in self.move_raw_ids) < sum(
                move.quantity_done for move in self.move_finished_ids):
            raise UserError('产出大于投入')

    def button_produce_finish(self):
        if self.is_multi_output:
            if self.is_force_output and sum(move.quantity_done for move in self.move_raw_ids) > sum(
                    move.quantity_done for move in self.move_finished_ids):
                raise UserError('尚未完全产出,不允许完成')
            self.post_inventory()
            if sum(move.quantity_done for move in self.move_raw_ids) == sum(
                    move.quantity_done for move in self.move_finished_ids):
                state = 'done'
            else:
                state = 'waiting_inventory_material'
            self.state = state
            return
        else:
            super(NewMrpProduction, self).button_produce_finish()

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
    def add_input_out_products(self):
        view = self.env.ref('linkloving_new_mrp.add_input_output_material_form')
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
                    'location_id': line.product_id.property_stock_production.id,
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

    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure',
        oldname='product_uom', readonly=True, required=False,
        states={'confirmed': [('readonly', False)]})

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
        return super(NewMrpProduction, self)._generate_raw_moves(exploded_lines)

    state = fields.Selection([
        ('draft', _('Draft')),
        ('confirmed', u'已排产'),
        ('waiting_material', _('Waiting Prepare Material')),
        ('prepare_material_ing', _('Material Preparing')),
        ('finish_prepare_material', _('Material Ready')),
        ('already_picking', _('Already Picking Material')),
        ('planned', 'Planned'),
        ('progress', '生产中'),
        ('waiting_inspection_finish', u'等待品检完成'),
        ('waiting_quality_inspection', _('Waiting Quality Inspection')),
        ('quality_inspection_ing', _('Under Quality Inspection')),
        ('waiting_rework', _('Waiting Rework')),
        ('rework_ing', _('Under Rework')),
        ('waiting_inventory_material', _('Waiting Inventory Material')),
        ('waiting_warehouse_inspection', _('Waiting Check Return Material')),
        ('waiting_post_inventory', _('Waiting Stock Transfers')),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='status',
        copy=False, default='draft', track_visibility='onchange')

    @api.multi
    def _generate_moves(self):
        print 'AAAAAAAAAAAAAAAAAAAAAAAAA'
        for production in self:


            production._generate_finished_moves()
            production._compute_done_stock_move_lines(production)
            if production.bom_id:
                factor = production.product_uom_id._compute_quantity(production.product_qty,
                                                                     production.bom_id.product_uom_id) / production.bom_id.product_qty
            else:
                factor = 1
            boms, lines = production.bom_id.explode(production.product_id, factor,
                                                    picking_type=production.bom_id.picking_type_id)
            production._generate_raw_moves(lines)
            # Check for all draft moves whether they are mto or not
            production._adjust_procure_method()
            production.move_raw_ids.action_confirm()
        return True

# class MrpProductionMaterial(models.Model):
#     _name = 'mrp.production.material'
#     product_id = fields.Many2one('product.product', string=u'产品', required=True)
#     # total_produce_qty = fields.Float(string=u'累计产出数量')
#     produce_qty = fields.Float(string=u'产出数量')
#
#     mo_id = fields.Many2one('mrp.production', on_delete='cascade')
#     type = fields.Selection([
#         ('input', '输入'),
#         ('output', '输出')
#     ])
