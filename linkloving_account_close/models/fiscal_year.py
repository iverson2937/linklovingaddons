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
                # 'fiscal_year_id': self.fiscal_year_id.id,
                'period_id': self.id,
                'debit': account.debit,
                'credit': account.credit
            })

        # self.state = 'done'
        data={}
        data['computed'] = {}

        obj_partner = self.env['res.partner']
        data['computed']['move_state'] = ['draft', 'posted']
        # if data['form'].get('target_move', 'all') == 'posted':
        data['computed']['move_state'] = ['posted']
        # if result_selection == 'supplier':
        #     data['computed']['ACCOUNT_TYPE'] = ['payable']
        # elif result_selection == 'customer':
        #     data['computed']['ACCOUNT_TYPE'] = ['receivable']
        # else:
        #查询所有
        data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']


        self.env.cr.execute("""
                    SELECT a.id
                    FROM account_account a
                    WHERE a.internal_type IN %s
                    AND NOT a.deprecated""", (tuple(['payable', 'receivable']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])]
        query = """
                    SELECT DISTINCT "account_move_line".partner_id
                    FROM "account_move_line", account_account AS account, account_move AS am
                    WHERE "account_move_line".partner_id IS NOT NULL
                        AND "account_move_line".account_id = account.id
                        AND am.state IN %s
                        AND "account_move_line".account_id IN %s
                        AND NOT account.deprecated
                        AND "account_move_line".reconciled = false"""
        self.env.cr.execute(query, tuple(params))
        partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref, x.name))
        for partner in partners:
            print partner.name
            self._sum_partner(data, partner)




    def _sum_partner(self, data, partner):

        result = 0.0
        # query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '

        params = [partner.id,  tuple(data['computed']['account_ids'])]
        query = """
        SELECT sum(credit),sum(debit)
                FROM "account_move_line"
                WHERE "account_move_line".partner_id = %s
                    AND account_id IN %s
                    """
        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        print contemp
        if contemp is not None:
            result = contemp[0] or 0.0
        return result
