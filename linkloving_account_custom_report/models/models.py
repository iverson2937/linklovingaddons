# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAccountReportWizard(models.TransientModel):
    _name = 'account.account.report.wizard'
    account_id = fields.Many2many('account.account')
    period_id = fields.Many2one('account.period')
