# -*- coding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    po_id = fields.Many2one('res.partner')