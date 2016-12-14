# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    partner_type = fields.Selection(selection_add=[('employee', 'employee')])



