# -*- coding: utf-8 -*-
import json


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp

class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    product_specs = fields.Text(string=u'产品规格', related='product_tmpl_id.product_specs')

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
                raise UserError(_('Recursion error!  A product with a Bill of Material should not have itself in its BoM or child BoMs!'))

            line_quantity = current_qty * current_line.product_qty #* (1 + bom_line.scrap_rate /100)
            bom = self._bom_find(product=current_line.product_id, picking_type=picking_type or self.picking_type_id, company_id=self.company_id.id)
            if bom.type == 'phantom':
                converted_line_quantity = current_line.product_uom_id._compute_quantity(line_quantity / bom.product_qty, bom.product_uom_id)
                bom_lines = [(line, current_line.product_id, converted_line_quantity, current_line) for line in bom.bom_line_ids] + bom_lines
                templates_done |= current_line.product_id.product_tmpl_id
                boms_done.append((bom, {'qty': converted_line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': current_line}))
            else:
                    lines_done.append((current_line, {'suggest_qty': line_quantity * (1 + bom_line.scrap_rate /100),'qty': line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': parent_line}))

        return boms_done, lines_done

class MrpBomLineExtend(models.Model):
    _inherit = 'mrp.bom.line'

    product_specs = fields.Text(string=u'产品规格', related='product_id.product_specs')
    scrap_rate = fields.Float(string=u'报废率(%)', default=3, )


    @api.multi
    def action_see_bom_structure_reverse(self):
        bom_tree_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_tree_view')
        bom_form_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_form_view')

        return {
            'name': _('逆展'),
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'view_id': bom_tree_view.id,
            'views': [(bom_tree_view.id, 'tree'), (bom_form_view.id, 'form')],
            'view_mode': 'tree',
            # 'view_type': 'form',
            'limit': 80,
            'context': {
            'search_default_bom_line_ids': self.product_id.default_code,}
        }


class StockMoveExtend(models.Model):
    _inherit = 'stock.move'

    qty_available = fields.Float(string=u'在手数量', related='product_id.qty_available')
    virtual_available = fields.Float(string=u'预测数量', related='product_id.virtual_available')
    suggest_qty =  fields.Float(string=u'建议数量', help=u'建议数量 = 实际数量 + 预计报废数量', )
    over_picking_qty = fields.Float(string=u'超领数量', )
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
        a = set(list) #不重复的set集合
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
    def _prepare_sim_stock_move_values(self,value):
        return {
            'product_id': value,
            'production_id': self.id
        }
    worker_line_ids = fields.One2many('worker.line', 'production_id')
    sim_stock_move_lines = fields.One2many('sim.stock.move', 'production_id')
    move_finished_ids = fields.One2many(
        'stock.move', 'production_id', 'Finished Products',
        copy=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain=[('scrapped', '=', False), ('is_return_material','=',False), ('is_over_picking', '=', False)])

    production_order_type = fields.Selection([('stockup',u'备货制（不需要产出全部数量）'),('ordering',u'订单制')], string=u'生产单类型', default='stockup',help=u'备货制：可产出任意数量的产品，便可完成生产，送往品检。\r\n订单制：必须产出生产单所需产品数量，才能进行下一步操作')

    state = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('waiting_material',u'等待备料'),
        ('prepare_material_ing',u'备料中...'),
        ('finish_prepare_material', u'备料完成'),
        ('already_picking', u'已领料'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('waiting_quality_inspection',u'等待品检'),
        ('quality_inspection_ing', u'品检中'),
        ('waiting_inventory_material',u'等待清点物料'),
        ('waiting_warehouse_inspection', u'等待检验物料'),
        ('waiting_post_inventory',u'等待入库'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, default='confirmed', track_visibility='onchange')


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
                   'res_id' : return_obj.id,
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

    #确认生产 等待备料
    def button_waiting_material(self):
        self.write({'state': 'waiting_material'})
        qty_wizard = self.env['change.production.qty'].create({
            'mo_id': self.id,
            'product_qty': self.product_qty,
        })
        qty_wizard.change_prod_qty()

    #开始备料
    def button_start_prepare_material(self):
        self.write({'state': 'prepare_material_ing'})
    #备料完成
    def button_finish_prepare_material(self):
        return self._show_picking_view(picking_mode='first_picking',invisible_options={'overpicking_invisible':True})
        # self.write({'state': 'finish_prepare_material'})
    #开始生产
    def button_start_produce(self):
        self.write({'state': 'progress'})

    #生产完成 等待品检
    def button_produce_finish(self):
        if self.qty_produced == 0:
            raise UserError(u'您还未产出任何产品，不可做此操作！')
        if not self.check_to_done and self.production_order_type == 'ordering':
            raise UserError(u'此生产单为订单制，需要产成所有数量的产品才能送往品检！')
        else:
            self.write({'state': 'waiting_quality_inspection'})


    #开始品检
    def button_start_quality_inspection(self):
        self.write({'state': 'quality_inspection_ing'})

    #品检通过
    def button_quality_inspection_success(self):
        self.write({'state': 'waiting_inventory_material'})
        # self.write({'state': 'waiting_post_inventory'}
    #清点物料
    def button_inventory_material(self):
        return self.button_return_material(need_create_one=True)
    #仓库清点物料
    def button_check_inventory_material(self):
        return self.button_return_material(need_create_one=False)
    #品检失败
    def button_quality_inspection_failed(self):
        self.write({'state': 'progress'})

    def picking_material(self):
        for move in self.sim_stock_move_lines:
            if move.over_picking_qty != 0:#如果超领数量不等于0
                new_move = move.stock_moves[0].copy(default={'quantity_done': move.over_picking_qty, 'product_uom_qty': move.over_picking_qty, 'production_id': move.production_id.id,
                                            'raw_material_production_id': move.raw_material_production_id.id,
                                            'procurement_id': move.procurement_id.id or False,
                                            'is_over_picking': True})
                move.production_id.move_raw_ids =  move.production_id.move_raw_ids + new_move
                move.over_picking_qty = 0
                new_move.write({'state':'assigned',})
            if self._context.get('picking_mode') == 'first_picking':#如果备料数量不等于0
                rounding = move.stock_moves[0].product_uom.rounding
                if float_compare(move.quantity_ready, move.stock_moves[0].product_uom_qty, precision_rounding=rounding) > 0:
                    qty_split =  move.stock_moves[0].product_uom._compute_quantity(move.quantity_ready - move.stock_moves[0].product_uom_qty,
                                                                   move.stock_moves[0].product_id.uom_id)

                    split_move = move.stock_moves[0].copy(
                        default={'quantity_done': qty_split, 'product_uom_qty':qty_split,
                                 'production_id': move.production_id.id,
                                 'raw_material_production_id': move.raw_material_production_id.id,
                                 'procurement_id': move.procurement_id.id or False,
                                 'is_over_picking': True})
                    move.production_id.move_raw_ids = move.production_id.move_raw_ids + split_move
                    split_move.write({'state': 'assigned', })
                    move.stock_moves[0].quantity_done = move.stock_moves[0].product_uom_qty
                else:
                    move.stock_moves[0].quantity_done = move.quantity_ready



        self.post_inventory()
        if self._context.get('picking_mode') == 'first_picking':
            self.write({'state': 'finish_prepare_material'})
            # elif self._context.get('picking_mode') == 'second_picking':
            # self.write({'state': 'already_picking'})
        return {'type' : 'ir.actions.act_window_close'}

    def button_fill_material(self):
        return self._show_picking_view(picking_mode='second_picking', invisible_options={'quantity_ready_invisible':True})

    #领料登记
    def button_already_picking(self):
        self.write({'state': 'already_picking'})
    # return self._show_picking_view(picking_mode='first_picking')

    def _show_picking_view(self, picking_mode,invisible_options):
        view = self.env.ref('linkloving_mrp_extend.picking_material_form')
        overpicking_invisible = invisible_options.get('overpicking_invisible',False)
        quantity_ready_invisible = invisible_options.get('quantity_ready_invisible',False)

        return {'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': self.id,
                'context': {'picking_mode' : picking_mode,
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
            'suggest_qty':  line_data['suggest_qty'],
        }
        return self.env['stock.move'].create(data)

    @api.multi
    def _update_raw_move(self, bom_line, line_data):
        quantity = line_data['qty']
        self.ensure_one()
        move = self.move_raw_ids.filtered(lambda x: x.bom_line_id.id == bom_line.id and x.state not in ('done', 'cancel'))
        if move:
            if quantity > 0:
                move[0].write({'product_uom_qty': quantity,
                               'suggest_qty': line_data['suggest_qty']})
            else:
                if move[0].quantity_done > 0:
                    raise UserError(_('Lines need to be deleted, but can not as you still have some quantities to consume in them. '))
                move[0].action_cancel()
                move[0].unlink()
            return move
        else:
            self._generate_raw_move(bom_line, line_data)

class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

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
        return self.env['stock.location'].search([('usage', '=', 'production')],limit=1)

    @api.model
    def _default_return_line(self):
        if self._context.get('active_id'):
            mrp_production_order = self.env['mrp.production'].browse(self._context['active_id'])
            product_ids = mrp_production_order.product_id.bom_ids[0].bom_line_ids.mapped(
            'product_id').ids
            lines = []
            for l in product_ids:
                obj = self.env['return.material.line'].create({
                    'return_qty' : 0,
                    'product_id' : l,
                    })
                lines.append(obj.id)
            return lines

    return_ids = fields.One2many('return.material.line','return_id', default=_default_return_line)
    name = fields.Char(
        'Reference',  default=lambda self: _('New'),
        copy=False, readonly=True, required=True,)
    owner_id = fields.Many2one('res.partner', 'Owner',)
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    # picking_id = fields.Many2one('stock.picking', 'Picking', states={'done': [('readonly', True)]})
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'production')]",
        required=True, default=_get_default_location_id)
    return_location_id = fields.Many2one(
        'stock.location', u'退料至...位置', default=_get_default_return_location_id,domain="[('usage', '=', 'internal')]",)
    return_qty = fields.Float(u'退料数量', default=0.0, required=True)
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
        return {'type':'ir.actions.act_window_close'}

    def _prepare_move_values(self, product):
        self.ensure_one()
        return {
            'name': self.name,
            'product_id': product.product_id.id,
            'product_uom': product.product_id.uom_id.id,
            'product_uom_qty': product.return_qty,
            'quantity_done' : product.return_qty,
            'location_id': self.location_id.id,
            'location_dest_id': self.return_location_id.id,
            'production_id' : self.production_id.id,
            'state': 'confirmed',
            'origin' : u'退料 %s' % self.production_id.name,
            'is_return_material' : True,
            # 'restrict_partner_id': self.owner_id.id,
            # 'picking_id': self.picking_id.id
        }

class ProductProductExtend(models.Model):
    _inherit = 'product.product'

    return_qty = fields.Float(string=u'退料数量',default=0 )

class WareHouseArea(models.Model):
    _name = 'warehouse.area'

    name = fields.Char(u'位置描述')


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

    product_id = fields.Many2one('product.product',)
    production_id = fields.Many2one('mrp.production')
    stock_moves = fields.One2many('stock.move', compute=_compute_stock_moves)
    raw_material_production_id = fields.Many2one('mrp.production',compute=_compute_raw_material_production_id)
    procurement_id = fields.Many2one('procurement.order', 'Procurement', compute=_compute_procurement_id)
    production_state = fields.Selection(related='production_id.state', readonly=True)

    quantity_done = fields.Float(default=0,compute=_compute_quantity_done)
    product_uom_qty = fields.Float(compute=_default_product_uom_qty)
    qty_available = fields.Float(compute=_default_qty_available)
    virtual_available = fields.Float(compute=_default_virtual_available)
    suggest_qty = fields.Float(compute=_default_suggest_qty)
    quantity_available = fields.Float(compute=_compute_quantity_available, )
    return_qty = fields.Float(compute=_compute_return_qty)
    over_picking_qty = fields.Float()
    quantity_ready = fields.Float()


class ReturnMaterialLine(models.Model):
    _name = 'return.material.line'

    product_id = fields.Many2one('product.product')
    return_qty = fields.Float(u'退料数量', readonly=False)
    return_id = fields.Many2one('mrp.return.material' )


class HrEmployeeExtend(models.Model):
    _inherit = 'hr.employee'

    is_worker = fields.Boolean(u'是否是工人', default=False)

#每个工人所处在的生产线
class LLWorkerLine(models.Model):
    _name = 'worker.line'

    worker_id = fields.Many2one('hr.employee')
    production_id = fields.Many2one('mrp.production', u'生产单')
    # unit_price = fields.Float(related='production_id.unit_price', string=u'单价')
    line_state = fields.Selection(
        [
            ('online',u'正常'),
            ('offline', u'请假'),
    ('outline', u'已退出'),
    ], default='online')

class LLWorkerTimeLine(models.Model):
    _name = 'worker.time.line'

    start_time = fields.Datetime(default=fields.datetime.now())
    end_time = fields.Datetime()
    worker_id = fields.Many2one('hr.employee')
    xishu = fields.Float(default=1.0)
    production_id = fields.Many2one('mrp.production', string=u'生产单')
    amount_of_money = fields.Float(default=0)



