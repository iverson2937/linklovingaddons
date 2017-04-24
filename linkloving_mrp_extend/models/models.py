# -*- coding: utf-8 -*-
import json
import datetime
import types

import jpush
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_compare, math
from odoo.addons import decimal_precision as dp


class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    product_specs = fields.Text(string=u'Product Specification', related='product_tmpl_id.product_specs')
    product_id = fields.Many2one(
        'product.product', 'Product Variant',
        domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]",
        help="If a product variant is defined the BOM is available only for this product.", copy=False)

    def explode(self, product, quantity, picking_type=False):
        """
            Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
            Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
            and converted into its UoM
        """
        boms_done = [(self, {'qty': quantity, 'product': product, 'original_qty': quantity, 'parent_line': False})]
        lines_done = []
        templates_done = product.product_tmpl_id

        bom_lines = [(bom_line, product, quantity, False) for bom_line in self.bom_line_ids]
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]

            if current_line._skip_bom_line(current_product):
                continue
            if current_line.product_id.product_tmpl_id in templates_done:
                raise UserError(_(
                    'Recursion error!  A product with a Bill of Material should not have itself in its BoM or child BoMs!'))

            line_quantity = current_qty * current_line.product_qty  # * (1 + bom_line.scrap_rate /100)
            bom = self._bom_find(product=current_line.product_id, picking_type=picking_type or self.picking_type_id,
                                 company_id=self.company_id.id)
            if bom.type == 'phantom':
                converted_line_quantity = current_line.product_uom_id._compute_quantity(line_quantity / bom.product_qty,
                                                                                        bom.product_uom_id)
                bom_lines = [(line, current_line.product_id, converted_line_quantity, current_line) for line in
                             bom.bom_line_ids] + bom_lines
                templates_done |= current_line.product_id.product_tmpl_id
                boms_done.append((bom,
                                  {'qty': converted_line_quantity, 'product': current_product, 'original_qty': quantity,
                                   'parent_line': current_line}))
            else:
                lines_done.append(
                    (current_line, {'suggest_qty': math.ceil(line_quantity * (1 + bom_line.scrap_rate / 100)),
                                    'qty': line_quantity, 'product': current_product,
                                    'original_qty': quantity, 'parent_line': parent_line}))

        return boms_done, lines_done


class MrpBomLineExtend(models.Model):
    _inherit = 'mrp.bom.line'

    product_specs = fields.Text(string='Product Specification', related='product_id.product_specs')
    scrap_rate = fields.Float(string='Scrap Rate(%)', default=3, )
    active1 = fields.Boolean(related='product_id.active')

    @api.multi
    def action_see_bom_structure_reverse(self):
        bom_tree_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_tree_view')
        bom_form_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_form_view')

        return {
            'name': _('Reverse Exhibition'),
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'view_id': bom_tree_view.id,
            'views': [(bom_tree_view.id, 'tree'), (bom_form_view.id, 'form')],
            'view_mode': 'tree',
            # 'view_type': 'form',
            'limit': 80,
            'context': {
                'search_default_bom_line_ids': self.product_id.default_code, }
        }


class ProductProductExtend(models.Model):
    _inherit = 'product.product'

    @api.multi
    def action_see_bom_structure_reverse(self):
        bom_tree_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_tree_view')
        bom_form_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_form_view')

        return {
            'name': _('Reverse Exhibition'),
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'view_id': bom_tree_view.id,
            'views': [(bom_tree_view.id, 'tree'), (bom_form_view.id, 'form')],
            'view_mode': 'tree',
            # 'view_type': 'form',
            'limit': 80,
            'context': {
                'search_default_bom_line_ids': self.product_tmpl_id.default_code, }
        }


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    @api.multi
    def action_see_bom_structure_reverse(self):
        bom_tree_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_tree_view')
        bom_form_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_form_view')

        return {
            'name': _('Reverse Exhibition'),
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'view_id': bom_tree_view.id,
            'views': [(bom_tree_view.id, 'tree'), (bom_form_view.id, 'form')],
            'view_mode': 'tree',
            # 'view_type': 'form',
            'limit': 80,
            'context': {
                'search_default_bom_line_ids': self.default_code, }
        }


class StockMoveExtend(models.Model):
    _inherit = 'stock.move'

    qty_available = fields.Float(string='On Hand', related='product_id.qty_available')
    virtual_available = fields.Float(string='Forecast Quantity', related='product_id.virtual_available')
    suggest_qty = fields.Integer(string='Suggest Quantity', help=u'建议数量 = 实际数量 + 预计报废数量', )
    over_picking_qty = fields.Float(string='Excess Quantity ', )
    is_return_material = fields.Boolean(default=False)
    is_over_picking = fields.Boolean(default=False)
    # @api.multi
    # def _qty_available(self):
    #     for move in self:
    #         # For consumables, state is available so availability = qty to do
    #         if move.state == 'assigned':
    #             move.quantity_available = move.product_uom_qty
    #         else:
    #             move.quantity_available = move.reserved_availability


class MrpProductionExtend(models.Model):
    _inherit = "mrp.production"

    availability = fields.Selection([
        ('assigned', _('Available')),
        ('partially_available', _('Partially Available')),
        ('waiting', _('Waiting')),
        ('none', 'None')], string=_('Material Status'),
        compute='_compute_availability', store=True)

    @api.depends('product_id.outgoing_qty', 'product_id.incoming_qty', 'product_id.qty_available')
    def _get_output_rate(self):
        for mo in self:
            if mo.product_id.outgoing_qty:
                rate = ((mo.product_id.incoming_qty + mo.product_id.qty_available) / mo.product_id.outgoing_qty)
                rate = round(rate, 2)

                mo.output_rate = (u"( 在制造量: " + "%s " + u"+库存:" + "%s ) /"u" 需求量：" + "%s = %s") % (
                    mo.product_id.incoming_qty, mo.product_id.qty_available, mo.product_id.outgoing_qty, rate)
            else:
                mo.output_rate = (u" 在制造量: " + "%s  " + u"库存:" + "%s  "u" 需求量：" + "%s  ") % (
                    mo.product_id.incoming_qty, mo.product_id.qty_available, mo.product_id.outgoing_qty)

    output_rate = fields.Char(compute=_get_output_rate, string=u'生产参考')

    @api.model
    def create(self, vals):
        res = super(MrpProductionExtend, self).create(vals)
        self._compute_sim_stock_move_lines(res)
        return res

    @api.multi
    def _compute_sim_stock_move_lines(self, new_pr):
        list = []
        for move in new_pr.move_raw_ids:
            list.append(move.product_id.id)
        a = set(list)  # 不重复的set集合
        res_list = []
        sim_stock_move_lines = self.env["sim.stock.move"].search([("production_id", "=", new_pr.id)])
        if not sim_stock_move_lines:
            for r in a:
                dict = self._prepare_sim_stock_move_values(r)
                res = self.env['sim.stock.move'].create(dict)
                res_list.append(res.id)
                new_pr.sim_stock_move_lines = res_list
        else:
            new_pr.sim_stock_move_lines = sim_stock_move_lines
            # else:
            #     for r in a:
            #         if r.product_id not in self.sim_stock_move_lines.mapped('product_id'):
            #             dict = self._prepare_sim_stock_move_values(r)
            #             res = self.env['sim.stock.move'].create(dict)
            #             self.sim_stock_move_lines |= res
            # return

    def _prepare_sim_stock_move_values(self, value):
        return {
            'product_id': value,
            'production_id': self.id
        }

    # 备料信息
    prepare_material_img = fields.Binary(string='Stock Image')
    prepare_material_area_id = fields.Many2one('stock.location.area', string='Area')
    #########
    # 送完品检时的信息
    to_qc_img = fields.Binary(string='Location Image')
    to_qc_area_id = fields.Many2one('stock.location.area', string='Area')
    #####
    # 品检反馈单
    qc_feedback_id = fields.Many2one('mrp.qc.feedback', string='QC Report')
    ####
    # 是否暂停
    is_pending = fields.Boolean()
    ####


    # @api.multi
    # def _compute_origin_sale_order_id(self):
    #     def get_parent_move(move):
    #         if move.move_dest_id:
    #             return get_parent_move(move.move_dest_id)
    #         return move
    #     for production in self:
    #         move = get_parent_move(production.move_finished_ids[0])
    #         production.origin_sale_order_id = move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.order_id.id or False
    #####
    worker_line_ids = fields.One2many('worker.line', 'production_id')
    sim_stock_move_lines = fields.One2many('sim.stock.move', 'production_id')
    move_finished_ids = fields.One2many(
        'stock.move', 'production_id', 'Finished Products',
        copy=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain=[('scrapped', '=', False), ('is_return_material', '=', False), ('is_over_picking', '=', False)])

    production_order_type = fields.Selection(
        [('stockup', 'By Stock（Unnecessary to output all quantity）'), ('ordering', u'By Order')], string=u'Order Type',
        default='stockup',
        help=u'By Stock：Can sent to QC check without complete  the Order。\nBy order：have to completed the Order then send to the QC station')
    total_spent_time = fields.Float(default=0, compute='_compute_total_spent_time', string='Time taken', )
    total_spent_money = fields.Float(default=0, compute='_compute_total_spent_money', string='Total Cost', )
    state = fields.Selection([
        ('draft', _('Draft')),
        ('confirmed', u'已排产'),
        ('waiting_material', _('Waiting Prepare Material')),
        ('prepare_material_ing', _('Material Preparing')),
        ('finish_prepare_material', _('Material Ready')),
        ('already_picking', _('Already Picking Material')),
        ('planned', 'Planned'),
        ('progress', '生产中'),
        ('waiting_quality_inspection', _('Waiting Quality Inspection')),
        ('quality_inspection_ing', _('Under Quality Inspection')),
        ('waiting_rework', _('Waiting Rework')),
        ('rework_ing', _('Under Rework')),
        ('waiting_inventory_material', _('Waiting Inventory Material')),
        ('waiting_warehouse_inspection', _('Waiting Check Return Material')),
        ('waiting_post_inventory', _('Waiting Stock Transfers')),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, default='confirmed', track_visibility='onchange')

    # 计算所有工人总共花的工时
    @api.one
    def _compute_total_spent_time(self):
        spent = 0
        for line in self.worker_line_ids:
            spent += line.cal_worker_spent_time()
        self.total_spent_time = spent / 3600.0

    # 计算生产总成本
    @api.one
    def _compute_total_spent_money(self):
        if self.mo_type == 'unit':  # 计件
            self.total_spent_money = self.qty_produced * self.unit_price
        elif self.mo_type == 'time':  # 计时
            self.total_spent_money = self.total_spent_time * self.hour_price
            # #添加工人

    # @api.multi
    # def add_worker(self):


    def button_return_material(self, need_create_one):
        view = self.env.ref('linkloving_mrp_extend.stock_return_material_form_view2')
        if not need_create_one:
            return_obj = self.env['mrp.return.material'].search([('production_id', '=', self.id)])[0]
            res = {'type': 'ir.actions.act_window',
                   'res_model': 'mrp.return.material',
                   'view_mode': 'form',
                   'view_id': view.id,
                   'res_id': return_obj.id,
                   'target': 'new'
                   }
        else:
            res = {'type': 'ir.actions.act_window',
                   'res_model': 'mrp.return.material',
                   'view_mode': 'form',
                   'view_id': view.id,
                   'target': 'new'}
            res['context'] = {'default_production_id': self.id,
                              'return_ids.product_ids': self.move_raw_ids.mapped('product_id').ids}
        return res

    # 确认生产 等待备料
    def button_waiting_material(self):
        self.write({'state': 'waiting_material'})
        qty_wizard = self.env['change.production.qty'].create({
            'mo_id': self.id,
            'product_qty': self.product_qty,
        })
        qty_wizard.change_prod_qty()
        # from linkloving_app_api.models.models import JPushExtend
        # JPushExtend.send_push(audience=jpush.audience(
        #     jpush.tag(LinklovingAppApi.get_jpush_tags("warehouse"))
        # ),notification=u"此订单已经可以开始备料")

    @api.multi
    def button_action_confirm_draft(self):
        for production in self:
            production.write({'state': 'confirmed'})

    # 开始备料
    def button_start_prepare_material(self):
        self.write({'state': 'prepare_material_ing'})

    # 备料完成
    def button_finish_prepare_material(self):
        return self._show_picking_view(picking_mode='first_picking', invisible_options={'overpicking_invisible': True})
        # self.write({'state': 'finish_prepare_material'})

    # 开始生产
    def button_start_produce(self):
        self.write({'state': 'progress'})

    # 给委外供应商发料
    def button_send_material_to_vendor(self):
        return {
            'name': u'填写物流单号',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'tracking.number.wizard',
            'target': 'new',
        }

        # 生产完成 等待品检

    def button_produce_finish(self):
        if self.qty_produced == 0:
            raise UserError(_('These is not output,can not finish the order!'))
        if not self.check_to_done and self.production_order_type == 'ordering':
            raise UserError(_('You have to complete the order before close it!'))
        else:
            # 生产完成 结算工时
            self.worker_line_ids.change_worker_state('outline')

            self.write({'state': 'waiting_quality_inspection'})

    # 开始品检
    def button_start_quality_inspection(self):
        self.write({'state': 'quality_inspection_ing'})

    # 品检通过
    def button_quality_inspection_success(self):
        self.write({'state': 'waiting_inventory_material'})
        # self.write({'state': 'waiting_post_inventory'}

    # 清点物料
    def button_inventory_material(self):
        return self.button_return_material(need_create_one=True)

    # 仓库清点物料
    def button_check_inventory_material(self):
        return self.button_return_material(need_create_one=False)

    # 品检失败,变为等待返工中
    def button_quality_inspection_failed(self):
        self.write({'state': 'waiting_rework'})
        # 开始返工   ,返工中

    def button_start_rework(self):
        self.write({'state': 'rework_ing'})

    def picking_material(self):
        if self._context.get('picking_mode') == 'first_picking':
            is_all_0 = True  # 是否全部为0，没有填写备料数量
            for move in self.sim_stock_move_lines:
                if move.quantity_ready != 0:
                    is_all_0 = False

            if is_all_0:
                raise UserError(u"请填写备料数量")
        for move in self.sim_stock_move_lines:
            if move.over_picking_qty != 0:  # 如果超领数量不等于0
                new_move = move.stock_moves[0].copy(
                    default={'quantity_done': move.over_picking_qty, 'product_uom_qty': move.over_picking_qty,
                             'production_id': move.production_id.id,
                             'raw_material_production_id': move.raw_material_production_id.id,
                             'procurement_id': move.procurement_id.id or False,
                             'is_over_picking': True})
                move.production_id.move_raw_ids = move.production_id.move_raw_ids + new_move
                move.over_picking_qty = 0
                new_move.write({'state': 'assigned', })
            if self._context.get('picking_mode') == 'first_picking':  # 如果备料数量不等于0
                if not move.stock_moves:
                    continue
                rounding = move.stock_moves[0].product_uom.rounding
                if float_compare(move.quantity_ready, move.stock_moves[0].product_uom_qty,
                                 precision_rounding=rounding) > 0:
                    qty_split = move.stock_moves[0].product_uom._compute_quantity(
                        move.quantity_ready - move.stock_moves[0].product_uom_qty,
                        move.stock_moves[0].product_id.uom_id)

                    split_move = move.stock_moves[0].copy(
                        default={'quantity_done': qty_split, 'product_uom_qty': qty_split,
                                 'production_id': move.production_id.id,
                                 'raw_material_production_id': move.raw_material_production_id.id,
                                 'procurement_id': move.procurement_id.id or False,
                                 'is_over_picking': True})
                    move.production_id.move_raw_ids = move.production_id.move_raw_ids + split_move
                    split_move.write({'state': 'assigned', })
                    move.stock_moves[0].quantity_done = move.stock_moves[0].product_uom_qty
                else:
                    move.stock_moves[0].quantity_done = move.quantity_ready

                # 备料完成,减去需求量
                move.product_id.qty_require -= move.stock_moves[0].product_uom_qty

        self.post_inventory()
        if self._context.get('picking_mode') == 'first_picking':
            self.write({'state': 'finish_prepare_material'})
            # elif self._context.get('picking_mode') == 'second_picking':
            # self.write({'state': 'already_picking'})
        return {'type': 'ir.actions.act_window_close'}

    def button_fill_material(self):
        return self._show_picking_view(picking_mode='second_picking',
                                       invisible_options={'quantity_ready_invisible': True})

    # 领料登记
    def button_already_picking(self):
        self.write({'state': 'already_picking'})

    # return self._show_picking_view(picking_mode='first_picking')

    def _show_picking_view(self, picking_mode, invisible_options):
        view = self.env.ref('linkloving_mrp_extend.picking_material_form')
        overpicking_invisible = invisible_options.get('overpicking_invisible', False)
        quantity_ready_invisible = invisible_options.get('quantity_ready_invisible', False)

        return {'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': self.id,
                'context': {'picking_mode': picking_mode,
                            'overpicking_invisible': overpicking_invisible,
                            'quantity_ready_invisible': quantity_ready_invisible},
                'target': 'new'}

    @api.multi
    def _generate_raw_move(self, bom_line, line_data):

        quantity = line_data['qty']
        # alt_op needed for the case when you explode phantom bom and all the lines will be consumed in the operation given by the parent bom line
        alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return self.env['stock.move']
        if bom_line.product_id.type not in ['product', 'consu']:
            return self.env['stock.move']
        if self.bom_id.routing_id and self.bom_id.routing_id.location_id:
            source_location = self.bom_id.routing_id.location_id
        else:
            source_location = self.location_src_id
        original_quantity = self.product_qty - self.qty_produced
        data = {
            'name': self.name,
            'date': self.date_planned_start,
            'bom_line_id': bom_line.id,
            'product_id': bom_line.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': bom_line.product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': bom_line.operation_id.id or alt_op,
            'price_unit': bom_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': quantity / original_quantity,
            'suggest_qty': line_data['suggest_qty'],
        }
        return self.env['stock.move'].create(data)

    @api.multi
    def update_rework_material(self, line, qty):
        quantity = line['product_qty']
        self.ensure_one()
        move = self.move_raw_ids.filtered(
            lambda x: x.product_id.id == line.product_id.id and x.state not in ('done', 'cancel'))
        if move:
            if quantity > 0:
                move[0].write({'product_uom_qty': quantity * qty,
                               'suggest_qty': math.ceil(quantity * qty)})
            else:
                if move[0].quantity_done > 0:
                    raise UserError(_(
                        'Lines need to be deleted, but can not as you still have some quantities to consume in them. '))
                move[0].action_cancel()
                move[0].unlink()
            return move

    @api.multi
    def _update_raw_move(self, bom_line, line_data):
        quantity = line_data['qty']
        self.ensure_one()
        move = self.move_raw_ids.filtered(
            lambda x: x.bom_line_id.id == bom_line.id and x.state not in ('done', 'cancel'))
        if move:
            if quantity > 0:
                move[0].write({'product_uom_qty': quantity,
                               'suggest_qty': line_data['suggest_qty']})
            else:
                if move[0].quantity_done > 0:
                    raise UserError(_(
                        'Lines need to be deleted, but can not as you still have some quantities to consume in them. '))
                move[0].action_cancel()
                move[0].unlink()
            return move
        else:
            self._generate_raw_move(bom_line, line_data)

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action

        """
        state = self._context.get('state')
        if state and state in ['finish_prepare_material', 'already_picking', 'progress', 'waiting_rework', 'rework_ing',
                               'waiting_inventory_material']:
            return [('state', '=', state), ('in_charge_id', '=', self.env.user.partner_id.id)]
        else:
            return [('state', '=', state)]


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

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
            if production.is_rework:
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


class ConfirmProduction(models.TransientModel):
    _name = 'confirm.production'

    mo_id = fields.Many2one('mrp.production', 'Manufacturing Order', required=True)
    product_qty = fields.Float(
        'Quantity To Produce',
        digits=dp.get_precision('Product Unit of Measure'), required=True)

    @api.model
    def default_get(self, fields):
        res = super(ConfirmProduction, self).default_get(fields)
        if 'mo_id' in fields and not res.get('mo_id') and self._context.get(
                'active_model') == 'mrp.production' and self._context.get('active_id'):
            res['mo_id'] = self._context['active_id']
        if 'product_qty' in fields and not res.get('product_qty') and res.get('mo_id'):
            res['product_qty'] = self.env['mrp.production'].browse(res.get['mo_id']).product_qty
        return res

    @api.multi
    def confirm_production(self):
        qty_wizard = self.env['change.production.qty'].create({
            'mo_id': self.mo_id.id,
            'product_qty': self.product_qty,
        })
        qty_wizard.change_prod_qty()


class MrpProductionProduceExtend(models.TransientModel):
    _inherit = 'mrp.product.produce'

    @api.multi
    def do_produce(self):
        # Nothing to do for lots since values are created using default data (stock.move.lots)
        moves = self.production_id.move_raw_ids
        quantity = self.product_qty
        if float_compare(quantity, 0, precision_rounding=self.product_uom_id.rounding) <= 0:
            raise UserError(_('You should at least produce some quantity'))
        for move in moves.filtered(lambda x: x.product_id.tracking == 'none' and x.state not in ('done', 'cancel')):
            if move.unit_factor:
                move.quantity_done_store += quantity * move.unit_factor
                # if move.product_id.virtual_available < 0:
                #     move.quantity_done_store = move.quantity_done_store / (1 + move.bom_line_id.scrap_rate / 100)
        moves = self.production_id.move_finished_ids.filtered(
            lambda x: x.product_id.tracking == 'none' and x.state not in ('done', 'cancel'))
        for move in moves:
            if move.product_id.id == self.production_id.product_id.id:
                move.quantity_done_store += quantity
            elif move.unit_factor:
                move.quantity_done_store += quantity * move.unit_factor
        self.check_finished_move_lots()
        if self.production_id.state == 'confirmed':
            self.production_id.state = 'progress'
        return {'type': 'ir.actions.act_window_close'}


class ReturnOfMaterial(models.Model):
    _name = 'mrp.return.material'

    def _get_default_return_location_id(self):
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)

    def _get_default_location_id(self):
        return self.env['stock.location'].search([('usage', '=', 'production')], limit=1)

    @api.model
    def _default_return_line(self):
        if self._context.get('active_id'):
            mrp_production_order = self.env['mrp.production'].browse(self._context['active_id'])
            if mrp_production_order.product_id.bom_ids:
                product_ids = mrp_production_order.product_id.bom_ids[0].bom_line_ids.mapped(
                    'product_id').ids
            lines = []
            for l in product_ids:
                obj = self.env['return.material.line'].create({
                    'return_qty': 0,
                    'product_id': l,
                })
                lines.append(obj.id)
            return lines

    return_ids = fields.One2many('return.material.line', 'return_id', default=_default_return_line)
    name = fields.Char(
        'Reference', default=lambda self: _('New'),
        copy=False, readonly=True, required=True, )
    owner_id = fields.Many2one('res.partner', 'Owner', )
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    # picking_id = fields.Many2one('stock.picking', 'Picking', states={'done': [('readonly', True)]})
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'production')]",
        required=True, default=_get_default_location_id)
    return_location_id = fields.Many2one(
        'stock.location', 'Return Location', default=_get_default_return_location_id,
        domain="[('usage', '=', 'internal')]", )
    return_qty = fields.Float('Return Quantity', default=0.0, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')], string='Status', default="draft")
    production_id = fields.Many2one('mrp.production', 'Production')

    @api.multi
    def do_return(self):
        if self._context.get('is_checking'):
            self.state = 'done'
        if self.state == 'done':
            for r in self.return_ids:
                if r.return_qty == 0:
                    continue
                move = self.env['stock.move'].create(self._prepare_move_values(r))
                r.return_qty = 0
                move.action_done()
            self.production_id.write({'state': 'waiting_post_inventory'})
        else:
            self.production_id.write({'state': 'waiting_warehouse_inspection'})
        return True

    @api.model
    def create(self, vals):
        obj = super(ReturnOfMaterial, self).create(vals)
        if vals.get('return_ids'):
            for return_id in vals['return_ids']:
                self.env['return.material.line'].browse(return_id[1]).return_id = obj.id
        return obj

    def action_done(self):
        self.do_return()
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_move_values(self, product):
        self.ensure_one()
        return {
            'name': self.name,
            'product_id': product.product_id.id,
            'product_uom': product.product_id.uom_id.id,
            'product_uom_qty': product.return_qty,
            'quantity_done': product.return_qty,
            'location_id': self.location_id.id,
            'location_dest_id': self.return_location_id.id,
            'production_id': self.production_id.id,
            'state': 'confirmed',
            'origin': 'Return %s' % self.production_id.name,
            'is_return_material': True,
            # 'restrict_partner_id': self.owner_id.id,
            # 'picking_id': self.picking_id.id
        }


class ProductProductExtend(models.Model):
    _inherit = 'product.product'

    return_qty = fields.Float(string='Return Quantity', default=0)


class WareHouseArea(models.Model):
    _name = 'warehouse.area'

    name = fields.Char('Location Description')


class SimStockMove(models.Model):
    _name = 'sim.stock.move'

    def _compute_stock_moves(self):
        for sim_move in self:
            sim_move.stock_moves = []
            for move in sim_move.production_id.move_raw_ids:
                if move.product_id == sim_move.product_id:
                    sim_move.stock_moves = sim_move.stock_moves + move

    def _compute_quantity_done(self):
        for sim_move in self:
            # move_to_fill = self.env['stock.move'].search([('production_id', '=', sim_move.production_id.id)])
            sim_move.quantity_done = 0
            for move in sim_move.production_id.move_raw_ids:
                if move.product_id == sim_move.product_id and not move.is_return_material:
                    sim_move.quantity_done += move.quantity_done

    def _default_product_uom_qty(self):
        for sim_move in self:
            if sim_move.stock_moves:
                for l in sim_move.stock_moves:
                    if l.is_over_picking or l.is_return_material:
                        continue
                    if l.state != "cancel":
                        sim_move.product_uom_qty += l.product_uom_qty

    def _default_qty_available(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.qty_available = sim_move.stock_moves[0].qty_available

    def _default_virtual_available(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.virtual_available = sim_move.stock_moves[0].virtual_available

    def _default_suggest_qty(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.suggest_qty = sim_move.stock_moves[0].suggest_qty

    def _compute_quantity_available(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.quantity_available = sim_move.stock_moves[0].quantity_available

    def _compute_return_qty(self):
        for sim_move in self:
            move_to_return = self.env['stock.move'].search([('production_id', '=', sim_move.production_id.id)])
            sim_move.return_qty = 0
            for move in move_to_return:
                if move.product_id == sim_move.product_id and move.is_return_material:
                    sim_move.return_qty += move.product_qty

    def _compute_raw_material_production_id(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.procurement_id = sim_move.stock_moves[0].procurement_id

    def _compute_procurement_id(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.raw_material_production_id = sim_move.stock_moves[0].raw_material_production_id

    @api.multi
    def _compute_product_type(self):
        location = self.env["stock.location"].search([("name", "=", "半成品流转库")], limit=1)
        if location and location.putaway_strategy_id and location.putaway_strategy_id.fixed_location_ids:
            fixed_location_ids = location.putaway_strategy_id.fixed_location_ids
        for sim in self:
            if sim.product_id.categ_id.id in fixed_location_ids.mapped("category_id").ids:
                sim.product_type = "semi-finished"
            else:
                sim.product_type = "material"

    product_id = fields.Many2one('product.product', )
    production_id = fields.Many2one('mrp.production')
    stock_moves = fields.One2many('stock.move', compute=_compute_stock_moves)
    raw_material_production_id = fields.Many2one('mrp.production', compute=_compute_raw_material_production_id)
    procurement_id = fields.Many2one('procurement.order', 'Procurement', compute=_compute_procurement_id)
    production_state = fields.Selection(related='production_id.state', readonly=True)

    quantity_done = fields.Float(default=0, compute=_compute_quantity_done)
    product_uom_qty = fields.Float(compute=_default_product_uom_qty)
    qty_available = fields.Float(compute=_default_qty_available)
    virtual_available = fields.Float(compute=_default_virtual_available)
    suggest_qty = fields.Integer(compute=_default_suggest_qty)
    quantity_available = fields.Float(compute=_compute_quantity_available, )
    return_qty = fields.Float(compute=_compute_return_qty)
    over_picking_qty = fields.Float()
    quantity_ready = fields.Float()
    area_id = fields.Many2one(related='product_id.area_id')
    product_type = fields.Selection(string="物料类型", selection=[('semi-finished', '半成品'), ('material', '原材料'), ],
                                    required=False, compute="_compute_product_type")

class ReturnMaterialLine(models.Model):
    _name = 'return.material.line'

    product_id = fields.Many2one('product.product')
    return_qty = fields.Float('Return Quantity', readonly=False)
    return_id = fields.Many2one('mrp.return.material')


class HrEmployeeExtend(models.Model):
    _inherit = 'hr.employee'

    is_worker = fields.Boolean('Is Worker', default=False)
    now_mo_id = fields.Many2one('mrp.production')


# 每个工人所处在的生产线
class LLWorkerLine(models.Model):
    _name = 'worker.line'

    @api.multi
    def _compute_amount_of_money(self):
        for one in self:
            one.amount_of_money = one.unit_price * one.xishu

    @api.multi
    def _compute_line_state(self):
        for line in self:
            if line.worker_time_line_ids:
                worker_time_line_ids_sorted = sorted(line.worker_time_line_ids, key=lambda d: d.start_time)
                line.line_state = worker_time_line_ids_sorted[len(worker_time_line_ids_sorted) - 1].state
            else:
                line.line_state = 'online'

    @api.multi
    def _compute_spent_time(self):
        for line in self:
            line.spent_time = line.cal_worker_spent_time() / 3600.0

    worker_id = fields.Many2one('hr.employee')
    production_id = fields.Many2one('mrp.production', 'Manufacturing Order')
    unit_price = fields.Float(related='production_id.unit_price', string='Unit Price')
    mo_type = fields.Selection(related='production_id.mo_type', string='Mo Type')
    xishu = fields.Float(default=1.0, string='Rate')
    amount_of_money = fields.Float(compute=_compute_amount_of_money)
    worker_time_line_ids = fields.One2many('worker.time.line', 'worker_line_id')
    spent_time = fields.Float(compute='_compute_spent_time')
    line_state = fields.Selection(
        [
            ('online', 'Normal'),
            ('offline', 'On Leave'),
            ('outline', 'Exit'),
        ], compute=_compute_line_state)

    def create_time_line(self):
        self.env['worker.time.line'].create({
            'worker_line_id': self.id,
            'start_time': fields.datetime.now(),
        })

    def get_newest_time_line(self):
        worker_time_line_ids_sorted = sorted(self.worker_time_line_ids, key=lambda d: d.start_time)
        return worker_time_line_ids_sorted[len(worker_time_line_ids_sorted) - 1]

    @api.multi
    def change_worker_state(self, state):
        for line in self:
            if not line.worker_time_line_ids:
                continue
            else:
                new_time_line = line.get_newest_time_line()
                if new_time_line.state != state:  # 若状态改变
                    if state == 'outline':
                        new_time_line.worker_id.now_mo_id = None
                    else:
                        new_time_line.worker_id.now_mo_id = new_time_line.production_id.id
                    new_time_line.offline_set_time()
                    self.env['worker.time.line'].create({
                        'start_time': fields.datetime.now(),
                        'worker_line_id': line.id,
                        'state': state,
                    })

    # 计算每个工人的所花费的时间
    # @api.multi
    def cal_worker_spent_time(self):
        # for worker_line in self:
        sum_time = 0
        for time_line in self.worker_time_line_ids:
            if time_line.state == 'online' and time_line.end_time:
                sum_time += time_line.cal_interval_of_time_line()

        return sum_time


class LLWorkerTimeLine(models.Model):
    _name = 'worker.time.line'

    start_time = fields.Datetime(default=fields.datetime.now())
    end_time = fields.Datetime()
    state = fields.Selection(
        [
            ('online', 'Normal'),
            ('offline', 'On leave'),
            ('outline', 'Exit'),
        ], default='online')

    worker_line_id = fields.Many2one('worker.line')
    worker_id = fields.Many2one(related='worker_line_id.worker_id', string="Worker")
    production_id = fields.Many2one(related='worker_line_id.production_id', string='Manufacturing Order')

    def offline_set_time(self):
        self.end_time = fields.datetime.now()

    def cal_interval_of_time_line(self):
        return (fields.Datetime.from_string(self.end_time) - fields.Datetime.from_string(self.start_time)).seconds


class MrpQcFeedBack(models.Model):
    _name = 'mrp.qc.feedback'

    @api.multi
    def _compute_qc_rate(self):
        for qc in self:
            if qc.qty_produced:
                qc.qc_rate = qc.qc_test_qty / qc.qty_produced * 100
            else:
                qc.qc_rate = 0

    @api.multi
    def _compute_qc_fail_rate(self):
        for qc in self:
            qc.qc_fail_rate = qc.qc_fail_qty / qc.qc_test_qty * 100

    production_id = fields.Many2one('mrp.production')
    qty_produced = fields.Float(related='production_id.qty_produced')
    qc_test_qty = fields.Float(string='Sampling Quantity')
    qc_rate = fields.Float(compute='_compute_qc_rate')
    qc_fail_qty = fields.Float('NG Quantity')
    qc_fail_rate = fields.Float('Defect Rate', compute='_compute_qc_fail_rate')
    qc_note = fields.Text(string='Note')
    qc_img = fields.Binary(string='Quality Inspection Image')

    product_id = fields.Many2one('production_id.product_id')


class MultiHandleWorker(models.TransientModel):
    _name = 'multi.handle.worker'

    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        employees = self.env['hr.employee'].search([('id', 'in', active_ids)])
        for em in employees:
            em.is_worker = True


class StcokPickingExtend(models.Model):
    _inherit = 'stock.picking'

    qc_note = fields.Text(string='Quality Inspection Image')
    qc_img = fields.Binary()
    post_img = fields.Binary()
    post_area_id = fields.Many2one('stock.location.area')
    express_img = fields.Binary("物流图片")


class ProcurementOrderExtend(models.Model):
    _inherit = 'procurement.order'

    def _prepare_mo_vals(self, bom):
        res = super(ProcurementOrderExtend, self)._prepare_mo_vals(bom)
        # 解析原单据
        self.parse_origin_and_update_dic(res)

        res.update({'state': 'draft',
                    'process_id': bom.process_id.id,
                    'unit_price': bom.process_id.unit_price,
                    'mo_type': bom.mo_type,
                    'hour_price': bom.hour_price,
                    'in_charge_id': bom.process_id.partner_id.id,
                    'product_qty': self.get_actual_require_qty(),
                    'date_planned_start': fields.Datetime.to_string(self._get_date_planned_from_today()),
                    })
        return res

    def _get_date_planned_from_today(self):
        format_date_planned = fields.Datetime.from_string(fields.Datetime.now())
        date_planned = format_date_planned - relativedelta(days=self.product_id.produce_delay or 0.0)
        date_planned = date_planned - relativedelta(days=self.company_id.manufacturing_lead)
        return date_planned

    def parse_origin_and_update_dic(self, dict):
        # 解析原单据
        if self.origin:
            origin_names = self.origin.split(":")
            sale_ret = self.env["sale.order"].search([("name", "in", origin_names)], limit=1)
            mo_ret = self.env["mrp.production"].search([("name", "in", origin_names)], limit=1)

            if sale_ret:
                dict.update({'origin_sale_id': sale_ret.id})
            if mo_ret:
                dict.update({'origin_mo_id': mo_ret.id})

    @api.multi
    def _prepare_purchase_order_line(self, po, supplier):
        product_new_qty = self.get_actual_require_qty()  #
        procurement_uom_po_qty = self.product_uom._compute_quantity(product_new_qty, self.product_id.uom_po_id)
        res = super(ProcurementOrderExtend, self)._prepare_purchase_order_line(po, supplier)

        self.parse_origin_and_update_dic(res)
        res.update({
            "product_qty": procurement_uom_po_qty
        })
        return res

    def get_draft_po_qty(self, product_id):
        pos = self.env["purchase.order"].search([("state", "in", ("make_by_mrp", "draft"))])
        chose_po_lines = self.env["purchase.order.line"]
        total_draft_order_qty = 0
        for po in pos:
            for po_line in po.order_line:
                if po_line.product_id.id == product_id.id:
                    chose_po_lines += po_line
                    total_draft_order_qty += po_line.product_qty
        return total_draft_order_qty

    def get_actual_require_qty(self):
        cur = datetime.datetime.now()
        print "-------------start time: %s" % cur
        if not self.rule_id:
            all_parent_location_ids = self._find_parent_locations()
            self.rule_id = self._search_suitable_rule([('location_id', 'in', all_parent_location_ids.ids)])
        extra_qty = 0
        if self.rule_id.action == "manufacture":
            OrderPoint = self.env['stock.warehouse.orderpoint'].search([("product_id", "=", self.product_id.id)],
                                                                       limit=1)
            if OrderPoint.product_min_qty != 0 or OrderPoint.product_max_qty != 0:
                extra_qty = self.product_id.outgoing_qty - self.product_id.incoming_qty - self.product_id.qty_available
        elif self.rule_id.action == "buy":
            extra_qty = self.get_draft_po_qty(self.product_id)
        sss = self.product_qty + self.product_id.outgoing_qty - self.product_id.incoming_qty - self.product_id.qty_available - extra_qty
        actual_need_qty = 0
        if sss > 0:
            actual_need_qty = sss

        cur = datetime.datetime.now()
        print "-------------end time: %s" % cur
        return actual_need_qty


class MultiSetMTO(models.TransientModel):
    _name = 'multi.set.mto'

    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        is_checked = context.get('is_checked', [])
        products = self.env['product.template'].search([('id', 'in', active_ids)])
        insert_type = 4 if is_checked else 2
        for product in products:
            product.route_ids = [(insert_type, self.env.ref('stock.route_warehouse0_mto').id)]


class purchase_order_extend(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def change_state_to_rfq(self):
        for po in self:
            po.state = "draft"

    def unlink_cancel_po(self):
        po_canceled = self.env["purchase.order"].search([("state", "=", "cancel")])
        mo_canceled = self.env["mrp.production"].search([("state", "=", "cancel")])
        po_canceled.unlink()
        mo_canceled.unlink()

    @api.multi
    def unlink(self):
        for order in self:
            if not order.state in ["cancel", "make_by_mrp"]:
                raise UserError(_('In order to delete a purchase order, you must cancel it first.'))
        super(models.Model, self).unlink()  ###注意 fixme
