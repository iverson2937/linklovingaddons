# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=False,
                                 domain=[('type', 'in', ('bank', 'cash'))])

    @api.model
    def _get_default_state(self):
        if self._context.get('apply'):
            return 'apply'
        else:
            return 'draft'

    state = fields.Selection(selection_add=[('apply', u'申请'), ('apply_confirm', u'确认申请')],
                             track_visibility='onchange', default=_get_default_state)

    def set_to_confirm(self):
        self.state = 'apply_confirm'

    def set_to_draft(self):
        self.state = 'draft'
