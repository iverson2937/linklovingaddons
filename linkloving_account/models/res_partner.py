# -*- coding: utf-8 -*-
from odoo import models, fields, api

from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    related_partner_id = fields.Many2one('res.partner', domain=[('is_company', '=', True)])

    def _find_accounting_partner(self, partner):
        ''' Find the partner for which the accounting entries will be created '''
        if partner.related_partner_id:
            return partner.related_partner_id
        return partner.commercial_partner_id
