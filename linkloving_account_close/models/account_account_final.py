# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountAccountFinal(models.Model):
    _name = "account.account.final"
    _description = "Final Account"
    _order = "create_date desc"
    name = fields.Char('Fiscal Year')
    account_id = fields.Many2one('account.account')
    partner_id = fields.Many2one('res.partner')
    fiscal_year_id = fields.Many2one('account.fiscalyear')
    period_id = fields.Many2one('account.period')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    start_debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    start_credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    year_debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    year_credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    end_debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    end_credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
