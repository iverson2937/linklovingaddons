# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from werkzeug import url_encode


class TrackingNumberWizard(models.TransientModel):
    _name = "tracking.number.wizard"
    _description = "Tracking Number"

    @api.model
    def _default_payment_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        mo = self.env['mrp.production'].browse(active_ids)
        return mo.id

    mo_id = fields.Many2one('mrp.production', default=_default_payment_id)
    tracking_number = fields.Char(string=u'物流单号')

    @api.multi
    def action_confirm(self):
        self.mo_id.tracking_number = self.tracking_number
        self.mo_id.state = 'progress'
        return {'type': 'ir.actions.act_window_close'}
