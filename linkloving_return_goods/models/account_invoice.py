# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    return_id = fields.Many2one('return.goods')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    return_line_id = fields.Many2one('return.goods.line')
