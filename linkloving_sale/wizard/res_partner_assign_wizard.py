# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import UserError


class SaleOrderCancel(models.TransientModel):
    """
    This wizard will cancel the mrp production
    """

    _name = "res.partner.assign.wizard"
    _description = "Assign Sales"
    user_id = fields.Many2one('res.users')

    @api.multi
    def action_apply(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['res.partner'].browse(active_ids):
            if record.customer and record.is_company:
                record.user_id = self.user_id.id
        return {'type': 'ir.actions.act_window_close'}
