# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'ir.needaction_mixin']
    tracking_number = fields.Char(string=u'Tracking Number')
    remark = fields.Text(string=u'备注', compute='_get_origin_number')

    @api.multi
    def check_purchase_order_line(self):
        """
        莫名其妙stock.move 没有purchase_line_id,重新赋值
        :return:
        """

        for picking in self:
            for move in picking.move_lines:
                line_id = self.env['purchase.order'].search([('name', '=', picking.origin)]).mapped(
                    'order_line').filtered(lambda x: x.product_id.id == move.product_id.id)
                if line_id:
                    move.purchase_line_id = line_id[0].id

    @api.multi
    def action_view_qc_result(self):
        view = self.env.ref('linkloving_mrp_extend.ll_stock_picking_pop_form')

        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': self.id,
                'target': 'new'}

    def reserveration_qty(self):
        self.ensure_one()
        operations = {}  # self.env['stock.pack.operation']
        moves_to_do = self.env['stock.move']
        main_domain = {}
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        for move in moves:
            if move.location_id.usage not in ('supplier', 'inventory', 'production'):
                ancestors = move.find_move_ancestors()
                if move.product_id.type != 'consu' or ancestors:
                    moves_to_do |= move
                    main_domain[move.id] = [('reservation_id', '!=', False), ('qty', '>', 0)]

                if move.state == 'waiting' and not ancestors:
                    # if the waiting move hasn't yet any ancestor (PO/MO not confirmed yet), don't find any quant available in stock
                    main_domain[move.id] += [('id', '=', False)]
                elif ancestors:
                    main_domain[move.id] += [('history_ids', 'in', ancestors.ids)]

                    # if the move is returned from another, restrict the choice of quants to the ones that follow the returned move
                if move.origin_returned_move_id:
                    main_domain[move.id] += [('history_ids', 'in', move.origin_returned_move_id.id)]
                for link in move.linked_move_operation_ids:
                    operations[move.id] = link.operation_id

        move_quants = {}
        for move in moves_to_do:
            stock_quant = self.env["stock.quant"]
            op = operations.get(move.id)
            pack_op_param = None
            lot_param = None
            if op:
                op.sorted(
                    key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (
                            x.pack_lot_ids and -1 or 0))
                for ops in op:
                    # TDE FIXME: this code seems to be in action_done, isn't it ?
                    # first try to find quants based on specific domains given by linked operations for the case where we want to rereserve according to existing pack operations
                    if not (ops.product_id and ops.pack_lot_ids):
                        for record in ops.linked_move_operation_ids:
                            move = record.move_id
                            if move.id in main_domain:
                                qty = record.qty
                                domain = main_domain[move.id]
                                if qty:
                                    pack_op_param = ops
                    else:
                        lot_qty = {}
                        rounding = ops.product_id.uom_id.rounding
                        for pack_lot in ops.pack_lot_ids:
                            lot_qty[pack_lot.lot_id.id] = ops.product_uom_id._compute_quantity(pack_lot.qty,
                                                                                               ops.product_id.uom_id)
                        for record in ops.linked_move_operation_ids:
                            move_qty = record.qty
                            move = record.move_id
                            for lot in lot_qty:
                                if float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0 and float_compare(
                                        move_qty, 0, precision_rounding=rounding) > 0:
                                    lot_param = lot
                                    continue
            domain = stock_quant._quants_get_reservation_domain(move,
                                                                lot_id=lot_param,
                                                                pack_operation_id=pack_op_param.id or False if pack_op_param else False,
                                                                company_id=self.env.context.get('company_id', False),
                                                                initial_domain=main_domain[move.id])
            removal_strategy = move.get_removal_strategy()
            if removal_strategy:
                order = self._quants_removal_get_order(removal_strategy)
            else:
                order = 'in_date'
            domain = domain if domain is not None else [('qty', '>', 0.0)]
            quants = stock_quant.search(domain, order=order)
            move_quants[move.id] = quants
        return move_quants

    def _quants_removal_get_order(self, removal_strategy=None):
        if removal_strategy == 'fifo':
            return 'in_date, id'
        elif removal_strategy == 'lifo':
            return 'in_date desc, id desc'
        raise UserError(_('Removal strategy %s not implemented.') % (removal_strategy,))

    @api.multi
    def unlink(self):
        self.mapped('pack_operation_product_ids').unlink()  # Checks if moves are not done
        return super(StockPicking, self).unlink()

    @api.multi
    def _get_origin_number(self):
        for picking in self:
            if picking.origin:

                if self.env['sale.order'].search([('name', '=', picking.origin)]):
                    so = self.env['sale.order'].search([('name', '=', picking.origin)])
                    picking.so_id = so.id
                    picking.remark = so.remark if so.remark else ''
                elif self.env['purchase.order'].search([('name', '=', picking.origin)]):
                    po = self.env['purchase.order'].search([('name', '=', picking.origin)])
                    picking.po_id = po.id
                    picking.remark = po.remark if po.remark else ''
                else:
                    picking.po_id = False
                    picking.so_id = False
                    picking.remark = ''

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
    complete_rate = fields.Integer(u"可用产品比率", compute="_compute_complete_rate", store=True)
    available_rate = fields.Integer(u"可用率", compute="_compute_available_rate")
    po_id = fields.Many2one('purchase.order', compute=_get_origin_number)
    so_id = fields.Many2one('sale.order', compute=_get_origin_number)
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
        self.state = 'validate'

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
    def _compute_available_rate(self):
        pickings = self.filtered(lambda move: move.state in ["waiting", "confirmed", "partially_available", "assigned"])

        for picking in pickings:
            quants = picking.reserveration_qty()
            total_quants_qty = {}
            for key in quants.keys():
                quant = quants[key].filtered(lambda x: x.reservation_id.id not in picking.move_lines.ids)
                total_quants_qty[key] = quant
            is_available = []
            for move in picking.move_lines:
                if move.state in ["cancel", "done"]:
                    continue
                sum_reserve_qty = sum(total_quants_qty.get(move.id).mapped("qty")) if total_quants_qty.get(
                    move.id) else 0
                if move.product_id.qty_available - sum_reserve_qty >= move.product_uom_qty:
                    is_available.append(True)
                else:
                    is_available.append(False)
            if all(is_available):  # 全是True
                picking.available_rate = 100
            else:
                true_len = 0
                for ava in is_available:
                    if ava:
                        true_len = true_len + 1
                if is_available:
                    picking.available_rate = int(true_len * 100 / len(is_available))
                else:
                    picking.available_rate = 0
                    # if move.product_id.qty_available > move.product_uom_qty:
                    #     require_qty += move.product_uom_qty
                    #     stock_qty += move.product_uom_qty
                    # else:
                    #     require_qty += move.product_uom_qty
                    #     stock_qty += move.product_id.qty_available

                    # stock_qty = stock_qty - total_quants_qty
                    # if require_qty != 0:
                    #     available_rate = int(stock_qty * 100 / require_qty)
                    #     if available_rate > 100:
                    #         available_rate = 100
                    #     elif available_rate < 0:
                    #         available_rate = 0
                    #     picking.available_rate = available_rate

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

    attachment_img_count = fields.Integer(compute='_compute_attachment_img_count', string=u'物流信息')
    qc_img_count = fields.Integer(compute='_compute_attachment_img_count', string=u'品检信息')

    def _compute_attachment_img_count(self):
        for attachment_one in self:
            attachment_one.attachment_img_count = len(
                # self.env['ir.attachment'].search(['&', ('res_id', '=', attachment_one.id), ('name', 'ilike', '物流')]))
                self.env['ir.attachment'].search([('res_id', '=', attachment_one.id)]))
            attachment_one.qc_img_count = len(
                self.env['ir.attachment'].search(
                    ['&', ('res_id', '=', attachment_one.id), ('name', 'ilike', 'Inspection')]))

    @api.multi
    def stock_img_count(self):

        type_btn = self._context.get('type_btn', False)
        action = self.env.ref('base.action_attachment').read()[0]
        # action['domain'] = [('partner_img_id', 'in', self.ids)]
        # action['domain'] = [('res_id', 'in', self.ids)]

        action['domain'] = [('res_id', 'in', self.ids)]

        if type_btn == "Inspection":
            action['domain'] = ['&', ('res_id', 'in', self.ids), ('name', 'ilike', type_btn)]

        return action


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    delivery_rule = fields.Selection(string=u"交货规则", selection=[('delivery_once', u'一次性发齐货'),
                                                                ('create_backorder', u'允许部分发货,并产生欠单'),
                                                                ('cancel_backorder', u'允许部分发货,不产生欠单')],
                                     required=False, default="delivery_once")


class StockMovePicking(models.Model):
    _inherit = "stock.move"

    data_type = fields.Float(string=u'数量', required=True, default=0.0, compute='_compute_qty')
    move_order_type = fields.Selection([
        ('procurement_warehousing', u'采购入库'), ('purchase_return', u'采购退货'),
        ('sell_return', u'销售退货'), ('sell_out', u'销售出库'),
        ('manufacturing_orders', u'制造入库'), ('manufacturing_picking', u'制造领料'), ('null', u' '),
        ('inventory_in', u'盘点入库'), ('inventory_out', u'盘点出库'), ('hand_movement_out', u'手动出库')
        , ('project_picking', u'工程领料'), ('manufacturing_rejected_out', u'清点退料'),
        ('manufacturing_mo_in', u'制造退料')], string=u'类型')

    reason_stock = fields.Text(string="操作原因")

    quantity_adjusted_qty = fields.Float(string=u'调整后数量')

    # traces_sort = fields.Integer(string=u'追溯界面排序')

    traces_sort_state = fields.Integer(string=u'追溯界面排序', compute='_compute_traces_sort', store=True)

    @api.depends('state')
    def _compute_traces_sort(self):
        for record in self:
            if record.state == 'done':
                record.traces_sort_state = 1
            elif record.state == 'assigned':
                record.traces_sort_state = 2
            elif record.state == 'confirmed':
                record.traces_sort_state = 3
            elif record.state == 'waiting':
                record.traces_sort_state = 4
            elif record.state == 'draft':
                record.traces_sort_state = 5
            elif record.state == 'cancel':
                record.traces_sort_state = 10

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

        self.data_type = self.product_uom_qty * sgin

    @api.model
    def create(self, vals):
        res = super(StockMovePicking, self).create(vals)
        # if res.quantity_adjusted_qty == 0:
        #     move_one = self.env['product.product'].browse(vals.get('product_id'))
        #     res.write({'quantity_adjusted_qty': move_one.qty_available})
        return res

    @api.multi
    def write(self, vals):
        res = super(StockMovePicking, self).write(vals)
        if vals.get("state") == 'done':
            for move in self:
                if move and move.state:
                    if move.state == 'done':
                        move.quantity_adjusted_qty = move.product_id.qty_available
        return res
