# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def _get_default_state(self):
        if self._context.get('apply'):
            return 'apply'
        else:
            return 'draft'

    state = fields.Selection(selection_add=[('apply', u'申请'), ('apply_confirm', u'确认申请')],
                             track_visibility='onchange', default=_get_default_state)
