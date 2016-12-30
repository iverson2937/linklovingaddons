# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountAccountFinal(models.Model):
    _name = "account.account.final"
    _description = "Final Account"
    _order = "create_date desc"
    name = fields.Char('Fiscal Year')
    account_id = fields.Many2one('account.account',string='科目')
    partner_id = fields.Many2one('res.partner')
    period_id = fields.Many2one('account.period',string='会计区间')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    # start_debit = fields.Monetary(default=0.0)
    # start_credit = fields.Monetary(default=0.0)
    # debit = fields.Monetary(default=0.0)
    # credit = fields.Monetary(default=0.0)
    # year_debit = fields.Monetary(default=0.0)
    # year_credit = fields.Monetary(default=0.0)
    # end_debit = fields.Monetary(default=0.0)
    # end_credit = fields.Monetary(default=0.0)

