# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'ir.needaction_mixin']
    tracking_number = fields.Char(string=u'快递单号')

    def _get_po_number(self):
        if self.origin:
            po = self.env['purchase.order'].search([('name', '=', self.origin)])
            self.po_id = po.id if po else None

    po_id = fields.Many2one('purchase.order', compute=_get_po_number)

    def _get_so_number(self):
        if self.origin:
            so = self.env['sale.order'].search([('name', '=', self.origin)])
            self.so_id = so.id if so else None

    po_id = fields.Many2one('purchase.order', compute=_get_so_number)

    so_id = fields.Many2one('sale.order', compute=_get_so_number)
    state = fields.Selection([
        ('draft', 'Draft'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('prepare', u'备货中'),
        ('post', u'备货完成'),
        ('qc_check', u'品检'),
        ('validate', u'待采购确认'),
        ('waiting_in', u'待入库'),
        ('waiting_out', u'待出库'),
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
    def start_prepare_stock(self):
        self.state = 'prepare'

    @api.multi
    def stock_ready(self):
        self.state = 'post'

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
                self.state = 'waiting_out'
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
