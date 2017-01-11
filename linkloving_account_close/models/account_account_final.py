# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountAccountFinal(models.Model):
    _name = "account.account.final"
    _description = "Final Account"
    _order = "period_id desc"
    account_id = fields.Many2one('account.account', string='科目')
    partner_id = fields.Many2one('res.partner')
    period_id = fields.Many2one('account.period', string='会计区间')
    fiscalyear_id = fields.Many2one('account.fiscalyear', related='period_id.fiscalyear_id', store=True)
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
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True,
                                          help='Utility field to express amount currency', store=True)
