# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountFiscalYear(models.Model):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"
    _order = "date_start, id"
    name = fields.Char('Fiscal Year', required=True)
    code = fields.Char('Code', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')

    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Close')
    ], default='open')

    @api.multi
    def create_period(self):
        period_obj = self.env['account.period']
        for fy in self:
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            period_obj.create({
                'name': "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                'code': ds.strftime('00/%Y'),
                'date_start': ds,
                'date_stop': ds,
                'special': True,
                'fiscalyear_id': fy.id,
            })
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=1, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=1)
        return True

    @api.multi
    def close_fiscal_year(self):
        pass


class AccountPeriod(models.Model):
    _name = 'account.period'

    _description = "Account period"
    name = fields.Char('Period Name', required=True)
    code = fields.Char('Code', size=12)
    date_start = fields.Date('Start of Period', required=True)
    date_stop = fields.Date('End of Period', required=True)
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', required=True, select=True)
    company_id = fields.Many2one(related='fiscalyear_id.company_id', string='Company', store=True, readonly=True)
    _order = "date_start"
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
    ]
    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Close')
    ], default='open')

    @api.multi
    def close_period(self):
        accounts = self.env['account.account'].search([])
        for account in accounts:
            self.env['account.account.final'].create({
                'account_id': account.id,
                'fiscal_year_id': self.fiscal_year_id.id,
                'period_id': self.id,
                'debit': account.debit,
                'credit': account.credit
            })

        self.state = 'done'
