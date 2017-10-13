# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'account.payment'
    prepayment_account_id = fields.Many2one('account.account')
