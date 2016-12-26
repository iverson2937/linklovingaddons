# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta


class account_fiscalyear(models.Model):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"
    name = fields.Char('Fiscal Year', required=True)
    code = fields.Char('Code', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,default=lambda self :self.env.user.company_id.id)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')
    _order = "date_start, id"

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


class AccountMoveLine(models.Model):
    @api.one
    def _period_get(self):


        period_id = self.env['account.period'].search([('date_start', '<=', self.date),
                                                                     ('date_stop', '>=', self.date),
                                                                     ('company_id', '=', self.company_id.id)],
                                                      limit=1
                                                           )
        self.period_id=period_id



    @api.one
    def _fiscalyear_get(self):

        fiscalyear_id = self.env['account.fiscalyear'].search([('date_start', '<=', self.date),
                                                                             ('date_stop', '>=', self.date),
                                                                             ('company_id', '=',
                                                                              self.company_id.id)], limit=1)

        return fiscalyear_id

    _inherit = 'account.move.line'

    period_id = fields.Many2one('account.period',compute=_period_get, store=False,
                                string='会计区间')
    fiscalyear_id = fields.Many2one('account.fiscalyear', compute=_fiscalyear_get, store=True,
                                    string='Fiscal Year')


class AccountInvoice(models.Model):
    @api.multi
    def _period_get(self):

        period_id = self.env.get('account.period').search([('date_start', '<=', self.date),
                                                           ('date_stop', '>=', self.date),
                                                           (
                                                               'company_id', '=',
                                                               self.company_id.id)],
                                                          limit=1
                                                          )
        return period_id

    _inherit = 'account.invoice'

    period_id = fields.Many2one('account.period', compute=_period_get, store=True, string='Period')
