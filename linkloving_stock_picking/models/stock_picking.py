# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit =['stock.picking','ir.needaction_mixin']
    po_id = fields.Many2one('purchase.order')
    so_id=fields.Many2one('sale.order')
    state = fields.Selection([
        ('draft', 'Draft'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('post', u'入库'),
        ('qc_check', u'品检'),
        ('validate', u'等待调拨'),
        ('done', 'Done')], string='Status', compute='_compute_state',
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
        self.state='qc_check'

    @api.multi
    def action_check_pass(self):
        self.state = 'validate'

    @api.multi
    def action_check_fail(self):
        self.state = 'assigned'

    @api.multi
    def set_to_available(self):
        self.state = 'assigned'



    @api.multi
    def reject(self):
        self.state = 'assigned'

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        return [('state', '=', 'validate'),('create_uid','=',self.env.user.id)]
