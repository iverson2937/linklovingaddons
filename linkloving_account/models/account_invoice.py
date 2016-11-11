# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentRegister(models.Model):
    _inherit = 'account.invoice'
    invoice = fields.Char(string='Invoice No')
