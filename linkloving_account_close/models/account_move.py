# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    period_id = fields.Many2one('account.period', string=u'会计区间',
                                domain=[('state', '!=', 'done')], copy=False,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                readonly=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_period(self):
        period_ids = self.env('account.period').search([('state', '!=', 'done')])
        return period_ids[0]

    period_id = fields.Many2one('account.period', string=u'会计区间',
                                domain=[('state', '!=', 'done')], copy=False,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                default=_get_period)
