# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_period(self):
        """
        Return  default account period value
        """
        account_period_obj = self.env['account.period']
        ids = account_period_obj.search([('state', '!=', 'done')])
        period_id = False
        if ids:
            period_id = ids[0]
        return period_id

    period_id = fields.Many2one('account.period', string=u'会计区间',
                                related='move_id.period_id',
                                domain=[('state', '!=', 'done')], copy=False,
                                required=True,
                                default=_get_period,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                readonly=False)




class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_period(self):
        """
        Return  default account period value
        """
        account_period_obj = self.env['account.period']
        ids = account_period_obj.search([('state','!=','done')])
        period_id = False
        if ids:
            period_id = ids[0]
        return period_id

    period_id = fields.Many2one('account.period', string=u'会计区间',
                                domain=[('state', '!=', 'done')], copy=False,
                                required=True,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                default=_get_period
                                )
