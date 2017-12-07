# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError


class AccountFiscalYear(models.Model):
    _name = "stock.picking"

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
                                domain=[('state', '!=', 'done')], copy=False,
                                required=True,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                default=_get_period
                                )
