# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'ir.needaction_mixin']
    tracking_number = fields.Char(string=u'Tracking Number')

    storage_type = fields.Selection([
        ('procurement_warehousing', '采购入库'),
        ('return_of_materials_to_storeroom', '退料入库'),
        ('return_storage', '退货入库'),
    ])

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

    delivery_rule = fields.Selection(compute="_compute_delivery_rule", selection=[('delivery_once', '一次性发齐货'),
                                                                                  ('create_backorder', '允许部分发货,并产生欠单'),
                                                                                  ('cancel_backorder', '允许部分发货,不产生欠单')],
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
        ('validate', u'待确认'),
        ('waiting_in', u'待入库'),
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

    delivery_rule = fields.Selection(string="交货规则", selection=[('delivery_once', '一次性发齐货'),
                                                               ('create_backorder', '允许部分发货,并产生欠单'),
                                                               ('cancel_backorder', '允许部分发货,不产生欠单')],
                                     required=False, default="delivery_once")


class SaleOrderExtend(models.Model):
    _inherit = "stock.move"

    data_type = fields.Float(string='数量', required=True, default=1.0, compute='_compute_prices')

    @api.one
    @api.depends('company_id')
    def _compute_prices(self):

        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
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

    def _get_domain_locations(self):
        '''
        Parses the context and returns a list of location_ids based on it.
        It will return all stock locations when no parameters are given
        Possible parameters are shop, warehouse, location, force_company, compute_child
        '''
        # TDE FIXME: clean that brol, context seems overused
        Warehouse = self.env['stock.warehouse']

        location_ids = []
        if self.env.context.get('location', False):
            if isinstance(self.env.context['location'], (int, long)):
                location_ids = [self.env.context['location']]
            elif isinstance(self.env.context['location'], basestring):
                domain = [('complete_name', 'ilike', self.env.context['location'])]
                if self.env.context.get('force_company', False):
                    domain += [('company_id', '=', self.env.context['force_company'])]
                location_ids = self.env['stock.location'].search(domain).ids
            else:
                location_ids = self.env.context['location']
        else:
            if self.env.context.get('warehouse', False):
                if isinstance(self.env.context['warehouse'], (int, long)):
                    wids = [self.env.context['warehouse']]
                elif isinstance(self.env.context['warehouse'], basestring):
                    domain = [('name', 'ilike', self.env.context['warehouse'])]
                    if self.env.context.get('force_company', False):
                        domain += [('company_id', '=', self.env.context['force_company'])]
                    wids = Warehouse.search(domain).ids
                else:
                    wids = self.env.context['warehouse']
            else:
                wids = Warehouse.search([]).ids

            for w in Warehouse.browse(wids):
                location_ids.append(w.view_location_id.id)
        return self._get_domain_locations_new(location_ids, company_id=self.env.context.get('force_company', False),
                                              compute_child=self.env.context.get('compute_child', True))

    def _get_domain_locations_new(self, location_ids, company_id=False, compute_child=True):
        operator = compute_child and 'child_of' or 'in'
        domain = company_id and ['&', ('company_id', '=', company_id)] or []
        locations = self.env['stock.location'].browse(location_ids)
        # TDE FIXME: should move the support of child_of + auto_join directly in expression
        # The code has been modified because having one location with parent_left being
        # 0 make the whole domain unusable
        hierarchical_locations = locations.filtered(
            lambda location: location.parent_left != 0 and operator == "child_of")
        other_locations = locations.filtered(
            lambda location: location not in hierarchical_locations)  # TDE: set - set ?
        loc_domain = []
        dest_loc_domain = []
        for location in hierarchical_locations:
            loc_domain = loc_domain and ['|'] + loc_domain or loc_domain
            loc_domain += ['&',
                           ('location_id.parent_left', '>=', location.parent_left),
                           ('location_id.parent_left', '<', location.parent_right)]
            dest_loc_domain = dest_loc_domain and ['|'] + dest_loc_domain or dest_loc_domain
            dest_loc_domain += ['&',
                                ('location_dest_id.parent_left', '>=', location.parent_left),
                                ('location_dest_id.parent_left', '<', location.parent_right)]
        if other_locations:
            loc_domain = loc_domain and ['|'] + loc_domain or loc_domain
            loc_domain = loc_domain + [('location_id', operator, [location.id for location in other_locations])]
            dest_loc_domain = dest_loc_domain and ['|'] + dest_loc_domain or dest_loc_domain
            dest_loc_domain = dest_loc_domain + [
                ('location_dest_id', operator, [location.id for location in other_locations])]
        return (
            domain + loc_domain,
            domain + dest_loc_domain + ['!'] + loc_domain if loc_domain else domain + dest_loc_domain,
            domain + loc_domain + ['!'] + dest_loc_domain if dest_loc_domain else domain + loc_domain
        )
