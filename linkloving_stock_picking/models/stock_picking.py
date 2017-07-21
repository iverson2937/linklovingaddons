# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'ir.needaction_mixin']
    tracking_number = fields.Char(string=u'Tracking Number')

    pick_order_type = fields.Selection([
        ('procurement_warehousing', u'采购入库'), ('purchase_return', u'采购退货'),
        ('sell_return', u'销售退货'), ('sell_out', u'销售出库'),
        ('manufacturing_orders', u'制造入库'), ('manufacturing_picking', u'制造领料'), ('null', u' '),
        ('inventory_in', u'盘点入库'), ('inventory_out', u'盘点出库')
    ], string=u"订单类型")

    @api.multi
    def action_view_qc_result(self):
        view = self.env.ref('linkloving_mrp_extend.ll_stock_picking_pop_form')

        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': self.id,
                'target': 'new'}

    @api.multi
    def unlink(self):
        self.mapped('pack_operation_product_ids').unlink()  # Checks if moves are not done
        return super(StockPicking, self).unlink()

    def _get_po_number(self):
        if self.origin:
            po = self.env['purchase.order'].search([('name', '=', self.origin)])
            self.po_id = po.id if po else None

    po_id = fields.Many2one('purchase.order', compute=_get_po_number)

    def _get_so_number(self):
        if self.origin:
            so = self.env['sale.order'].search([('name', '=', self.origin)])
            self.so_id = so.id if so else None

    @api.multi
    def _compute_delivery_rule(self):
        for picking in self:
            for move in picking.move_lines:
                if move.procurement_id.sale_line_id:
                    sale_id = move.procurement_id.sale_line_id.order_id
                    picking.delivery_rule = sale_id.delivery_rule
                    break

    delivery_rule = fields.Selection(compute="_compute_delivery_rule", selection=[('delivery_once', u'一次性发齐货'),
                                                                                  ('create_backorder', u'允许部分发货,并产生欠单'),
                                                                                  (
                                                                                      'cancel_backorder',
                                                                                      u'允许部分发货,不产生欠单')],
                                     )

    # actual_state = fields.Selection(string="", selection=[('', ''), ('', ''), ], required=False, )
    complete_rate = fields.Integer("可用产品比率", compute="_compute_complete_rate", store=True)

    po_id = fields.Many2one('purchase.order', compute=_get_so_number)
    so_id = fields.Many2one('sale.order', compute=_get_so_number)
    state = fields.Selection([
        ('draft', 'Draft'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('qc_check', u'品检'),
        ('validate', u'采购确认'),
        ('waiting_in', u'入库'),
        ('done', 'Done'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n"
             " * Waiting Availability: still waiting for the availability of products\n"
             " * Partially Available: some products are available and reserved\n"
             " * Ready to Transfer: products reserved, simply waiting for confirmation.\n"
             " * Transferred: has been processed, can't be modified or cancelled anymore\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore")

    @api.multi
    def action_post(self):
        self.state = 'qc_check'

    @api.multi
    def action_check_pass(self):
        self.state = 'validate'

    @api.multi
    def action_check_fail(self):
        self.state = 'assigned'

    @api.multi
    def to_stock(self):
        self.state = 'done'

    @api.multi
    def reject(self):
        self.state = 'assigned'

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        if self._context.get('picking_type_code') == 'incoming':

            return [('state', '=', 'validate'), ('create_uid', '=', self.env.user.id)]
        elif self._context.get('picking_type_code') == 'outgoing':
            return [('state', '=', 'post'), ('create_uid', '=', self.env.user.id)]

    @api.depends('move_type', 'launch_pack_operations', 'move_lines.state', 'move_lines.picking_id',
                 'move_lines.partially_available')
    @api.one
    def _compute_state(self):
        ''' State of a picking depends on the state of its related stock.move
         - no moves: draft or assigned (launch_pack_operations)
         - all moves canceled: cancel
         - all moves done (including possible canceled): done
         - All at once picking: least of confirmed / waiting / assigned
         - Partial picking
          - all moves assigned: assigned
          - one of the move is assigned or partially available: partially available
          - otherwise in waiting or confirmed state
        '''
        if not self.move_lines and self.launch_pack_operations:
            self.state = 'assigned'
        elif not self.move_lines:
            self.state = 'draft'
        elif any(move.state == 'draft' for move in self.move_lines):  # TDE FIXME: should be all ?
            self.state = 'draft'
        elif all(move.state == 'cancel' for move in self.move_lines):
            self.state = 'cancel'
        elif all(move.state in ['cancel', 'done'] for move in self.move_lines):
            if self.picking_type_code == 'incoming':
                self.state = 'waiting_in'
            else:
                self.state = 'done'
        else:
            # We sort our moves by importance of state: "confirmed" should be first, then we'll have
            # "waiting" and finally "assigned" at the end.
            moves_todo = self.move_lines \
                .filtered(lambda move: move.state not in ['cancel', 'done']) \
                .sorted(key=lambda move: (move.state == 'assigned' and 2) or (move.state == 'waiting' and 1) or 0)
            if self.move_type == 'one':
                self.state = moves_todo[0].state
            elif moves_todo[0].state != 'assigned' and any(
                            x.partially_available or x.state == 'assigned' for x in moves_todo):
                self.state = 'partially_available'
            else:
                self.state = moves_todo[-1].state

    @api.multi
    def _compute_complete_rate(self):
        computed_result = {}
        # pickings = self.env["stock.picking"].search([("state", "in", ["waiting", "partially_available", "assigned"])])
        pickings = self.filtered(lambda move: move.state not in [
            ("state", "in", ["waiting", "partially_available", "assigned"])])
        for picking in pickings:

            if picking.move_lines:
                require_qty = 0
                stock_qty = 0
                for move in picking.move_lines:
                    if move.state in ["cancel", "done"]:
                        continue
                    if move.product_id.qty_available > move.product_uom_qty:
                        require_qty += move.product_uom_qty
                        stock_qty += move.product_uom_qty
                    else:
                        require_qty += move.product_uom_qty
                        stock_qty += move.product_id.qty_available
                if require_qty != 0:
                    picking.complete_rate = int(stock_qty * 100 / require_qty)
                else:
                    picking.complete_rate = 0

    @api.multi
    def is_start_prepare(self):
        picking_un_start_prepare = self.env["stock.picking"]
        for pick in self:
            if sum(pick.pack_operation_product_ids.mapped("qty_done")) == 0:  # 已经备货 不能取消保留
                picking_un_start_prepare += pick
        return picking_un_start_prepare

    @api.multi
    def contain_product(self, product):
        picking_contain = self.env["stock.picking"]
        for pick in self:
            if product.id in pick.move_lines.mapped("product_id").ids:
                picking_contain += pick
        return picking_contain


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    delivery_rule = fields.Selection(string=u"交货规则", selection=[('delivery_once', u'一次性发齐货'),
                                                                ('create_backorder', u'允许部分发货,并产生欠单'),
                                                                ('cancel_backorder', u'允许部分发货,不产生欠单')],
                                     required=False, default="delivery_once")


class StockMovePicking(models.Model):
    _inherit = "stock.move"

    data_type = fields.Float(string=u'数量', required=True, default=0.0, compute='_compute_qty')
    stock_type = fields.Char(string=u'出/入库', compute='_compute_qty', store=True)
    stock_types = fields.Char(string=u'出/入库', compute='_compute_qty')
    move_order_type = fields.Selection([
        ('procurement_warehousing', u'采购入库'), ('purchase_return', u'采购退货'),
        ('sell_return', u'销售退货'), ('sell_out', u'销售出库'),
        ('manufacturing_orders', u'制造入库'), ('manufacturing_picking', u'制造领料'), ('null', u' '),
        ('inventory_in', u'盘点入库'), ('inventory_out', u'盘点出库')
    ], string=u'类型')

    reason_stock = fields.Text(string="操作原因")

    @api.one
    @api.depends('company_id')
    def _compute_qty(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self.env['product.product']._get_domain_locations()
        domain_move_in_todo = [('state', 'in', ['done'])] + [
            ('product_id', 'in', [self.product_id.id])] + domain_move_in_loc
        domain_move_out_todo = [('state', 'in', ['done'])] + [
            ('product_id', 'in', [self.product_id.id])] + domain_move_out_loc
        Move = self.env['stock.move']
        # 共接收数量
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in
                            Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id']))
        # 共支出数量
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in
                             Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id']))
        sgin = 1
        if self in self.product_id.env['stock.move'].search(domain_move_out_todo):
            sgin = -1
            self.stock_types = "出库"
            self.write({'stock_type': '出库'})

        if self in self.product_id.env['stock.move'].search(domain_move_in_todo):
            self.stock_types = "入库"
            self.write({'stock_type': '入库'})

        self.data_type = self.product_uom_qty * sgin

