# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    period_id = fields.Many2one('account.period', compute='_get_period', store=True)

    @api.multi
    @api.depends('move_line_ids.period_id')
    def _get_period(self):
        for payment in self:

            if payment.move_line_ids:
                payment.period_id = payment.move_line_ids[0].period_id.id
