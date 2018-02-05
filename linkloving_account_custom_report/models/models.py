# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAccountReportWizard(models.TransientModel):
    _name = 'account.account.report.wizard'
    account_ids = fields.Many2many('account.account')
    fiscal_year_id = fields.Many2one('account.fiscalyear')
    period_id_start = fields.Many2one('account.period')
    period_id_end = fields.Many2one('account.period')
