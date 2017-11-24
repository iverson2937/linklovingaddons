# -*- coding: utf-8 -*-
from odoo import models, fields, api

from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    related_partner_id = fields.Many2one('res.partner', domain=[('is_company', '=', True)])
    account_payment_ids = fields.One2many('account.payment', 'partner_id')

    def _find_accounting_partner(self, partner):
        ''' Find the partner for which the accounting entries will be created '''
        if partner.related_partner_id:
            return partner.related_partner_id
        return partner.commercial_partner_id

    @api.multi
    def _compute_account_payment_count(self):

        for res in self:
            res.update({
                'account_payment_count': len(set(res.account_payment_ids.ids))
            })

    account_payment_count = fields.Integer(compute=_compute_account_payment_count)
