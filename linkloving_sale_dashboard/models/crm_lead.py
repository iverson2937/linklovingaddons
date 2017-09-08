# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def retrieve_sales_dashboard(self):
        res = super(CrmLead, self).retrieve_sales_dashboard()
        domain = [('state', '=', 'confirm')]
        res['payment_count'] = self.env['account.payment'].search_count(domain)
        return res
