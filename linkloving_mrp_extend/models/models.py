# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp

class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    product_specs = fields.Text(string=u'产品规格', related='product_tmpl_id.product_specs')

    # def explode(self, product, quantity, picking_type=False):
    #     """
    #         Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
    #         Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
    #         and converted into its UoM
    #     """
    #     boms_done = [(self, {'qty': quantity, 'product': product, 'original_qty': quantity, 'parent_line': False})]
    #     lines_done = []
    #     templates_done = product.product_tmpl_id
    #
    #     bom_lines = [(bom_line, product, quantity, False) for bom_line in self.bom_line_ids]
    #     while bom_lines:
    #         current_line, current_product, current_qty, parent_line = bom_lines[0]
    #         bom_lines = bom_lines[1:]
    #
    #         if current_line._skip_bom_line(current_product):
    #             continue
    #         if current_line.product_id.product_tmpl_id in templates_done:
    #             raise UserError(_('Recursion error!  A product with a Bill of Material should not have itself in its BoM or child BoMs!'))
    #
    #         line_quantity = current_qty * current_line.product_qty * (1 + bom_line.scrap_rate /100)
    #         bom = self._bom_find(product=current_line.product_id, picking_type=picking_type or self.picking_type_id, company_id=self.company_id.id)
    #         if bom.type == 'phantom':
    #             converted_line_quantity = current_line.product_uom_id._compute_quantity(line_quantity / bom.product_qty, bom.product_uom_id)
    #             bom_lines = [(line, current_line.product_id, converted_line_quantity, current_line) for line in bom.bom_line_ids] + bom_lines
    #             templates_done |= current_line.product_id.product_tmpl_id
    #             boms_done.append((bom, {'qty': converted_line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': current_line}))
    #         else:
    #                 lines_done.append((current_line, {'qty': line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': parent_line}))
    #
    #     return boms_done, lines_done

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

    qty_available = fields.Float(string='在手数量', related='product_id.qty_available')
    virtual_available = fields.Float(string='预测数量', related='product_id.virtual_available')

    # @api.multi
    # def _qty_available(self):
    #     for move in self:
    #         # For consumables, state is available so availability = qty to do
    #         if move.state == 'assigned':
    #             move.quantity_available = move.product_uom_qty
    #         else:
    #             move.quantity_available = move.reserved_availability


class MrpProductionExtend(models.Model):
    _inherit = 'mrp.production'

    # @api.multi
    # def _get_produced_qty(self):
    #     for production in self:
    #         production.check_to_done_new = production.check_to_done
    #         if production.check_to_done_new:
    #             production.write({'state' : 'waiting_quality_inspection'})

    # check_to_done_new = fields.Boolean(computed='_get_check_to_done', )
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
        ('back_to_factory_ing',u'返工中'),
        ('waiting_post_inventory',u'等待入库'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, default='confirmed', track_visibility='onchange')


    def button_return_material(self):
        view = self.env.ref('linkloving_mrp_extend.stock_return_material_form_view2')
        res = {'type': 'ir.actions.act_window',
               'res_model': 'mrp.return.material',
               'view_mode': 'form',
               'view_id': view.id,
               'target': 'new'}
        res['context'] = {'default_production_id': self.id,
                          'product_ids': self.move_raw_ids.mapped('product_id').ids}
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
        self.write({'state': 'finish_prepare_material'})
    #开始生产
    def button_start_produce(self):
        self.write({'state': 'progress'})

    #生产完成 等待品检
    def button_produce_finish(self):
        self.write({'state': 'waiting_quality_inspection'})

    #开始品检
    def button_start_quality_inspection(self):
        self.write({'state': 'quality_inspection_ing'})

    #品检通过
    def button_quality_inspection_success(self):
        self.write({'state': 'waiting_post_inventory'})
    #品检失败
    def button_quality_inspection_failed(self):
        self.write({'state': 'progress'})

    def picking_material(self):
        for move in self.move_raw_ids:
            move.write({'state':'assigned',})
        self.post_inventory()
        if self._context.get('picking_mode') == 'first_picking':
            self.write({'state': 'already_picking'})
            # elif self._context.get('picking_mode') == 'second_picking':
            # self.write({'state': 'already_picking'})
        return {'type' : 'ir.actions.act_window_close'}

    def button_fill_material(self):
        return self._show_picking_view(picking_mode='second_picking')

    #领料登记
    def button_already_picking(self):
        # self.write({'state': 'progress'})
        return self._show_picking_view(picking_mode='first_picking')

    def _show_picking_view(self, picking_mode):
        view = self.env.ref('linkloving_mrp_extend.picking_material_form')
        return {'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': self.id,
                'context': {'picking_mode' : picking_mode},
                'target': 'new'}
        # def _generate_raw_move(self, bom_line, line_data):
        #     quantity = line_data['qty']
        #     quantity = quantity + quantity * bom_line.scrap_rate / 100
        #     line_data['qty'] = quantity
        #     return super(MrpProductionExtend, self)._generate_raw_move(bom_line, line_data)

        # @api.multi
        # def _update_raw_move(self, bom_line, line_data):
        #     quantity = line_data['qty']
        #     quantity = quantity + quantity * bom_line.scrap_rate / 100
        #     line_data['qty'] = quantity
        #     return super(MrpProductionExtend, self)._update_raw_move(bom_line, line_data)

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

class MrpProductionExtend(models.TransientModel):
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

class ReturnOfMaterial(models.TransientModel):
    _name = 'mrp.return.material'

    def _get_default_return_location_id(self):
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)

    def _get_default_location_id(self):
        return self.env['stock.location'].search([('usage', '=', 'production')],limit=1)

    product_id = fields.Many2one(
        'product.product', 'Product',
        required=True, states={'done': [('readonly', True)]})
    name = fields.Char(
        'Reference',  default=lambda self: _('New'),
        copy=False, readonly=True, required=True,
        states={'done': [('readonly', True)]})
    owner_id = fields.Many2one('res.partner', 'Owner', states={'done': [('readonly', True)]})
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    # picking_id = fields.Many2one('stock.picking', 'Picking', states={'done': [('readonly', True)]})
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'production')]",
        required=True, states={'done': [('readonly', True)]}, default=_get_default_location_id)
    return_location_id = fields.Many2one(
        'stock.location', u'退料至...位置', default=_get_default_return_location_id,domain="[('usage', '=', 'internal')]",
        states={'done': [('readonly', True)]})
    return_qty = fields.Float('Quantity', default=1.0, required=True, states={'done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')], string='Status', default="draft")
    production_id = fields.Many2one('mrp.production', 'Production')

    @api.multi
    def do_return(self):
        for r in self:
            move = self.env['stock.move'].create(r._prepare_move_values())
            move.action_done()
            r.write({'move_id': move.id, 'state': 'done'})
        return True

    @api.model
    def create(self, vals):
        obj = super(ReturnOfMaterial, self).create(vals)
        obj.do_return()
        return obj

    def action_done(self):
        return {'type':'ir.actions.act_window_close'}
    def _prepare_move_values(self):
        self.ensure_one()
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': self.return_qty,
            'quantity_done' : self.return_qty,
            'location_id': self.location_id.id,
            'location_dest_id': self.return_location_id.id,
            'production_id' : self.production_id.id,
            'state': 'confirmed',
            'origin' : u'退料 %s' % self.production_id.name,
            # 'restrict_partner_id': self.owner_id.id,
            # 'picking_id': self.picking_id.id
        }