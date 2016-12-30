# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    period_id = fields.Many2one('account.period', string=u'会计区间',
                                domain=[('state', '!=', 'done')], copy=False,
                                required=True,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                readonly=False)
    fiscalyear_id = fields.Many2one('account.fiscalyear')


class AccountMove(models.Model):
    _inherit = 'account.move'

    period_id = fields.Many2one('account.period', string=u'会计区间',
                                domain=[('state', '!=', 'done')], copy=False,
                                required=True,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                )
