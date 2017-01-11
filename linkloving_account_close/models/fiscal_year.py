# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError


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
            # period_obj.create({
            #     'name': "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
            #     'code': ds.strftime('00/%Y'),
            #     'date_start': ds,
            #     'date_stop': ds,
            #     'special': True,
            #     'fiscalyear_id': fy.id,
            # })
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
    def unlink(self):
        if self.env['account.move.line'].search([('period_id','=',self.id)]):
            raise UserError(u'此会计区间已经有分录生产，不可以删除')
        return super(AccountPeriod, self).unlink()


    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = (
        "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
        " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result.keys():
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            if display_account == 'all':
                account_res.append(res)
            if display_account in ['movement', 'not_zero'] and not currency.is_zero(res['balance']):
                account_res.append(res)
        return account_res


    @api.multi
    def close_period(self):
        accounts=self.env['account.account'].search([])


        # self.state='done'
        # # self.state = 'done'
        # data={}
        # data['computed'] = {}
        #
        # obj_partner = self.env['res.partner']
        #
        # # if data['form'].get('target_move', 'all') == 'posted':
        # data['computed']['move_state'] = ['posted']
        # # if result_selection == 'supplier':
        # #     data['computed']['ACCOUNT_TYPE'] = ['payable']
        # # elif result_selection == 'customer':
        # #     data['computed']['ACCOUNT_TYPE'] = ['receivable']
        # # else:
        # #查询所有
        # data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']
        #
        #
        # self.env.cr.execute("""
        #             SELECT a.id
        #             FROM account_account a
        #             WHERE a.internal_type IN %s
        #             AND NOT a.deprecated""", (tuple(['payable', 'receivable']),))
        # data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        # params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])]
        # query = """
        #             SELECT DISTINCT "account_move_line".partner_id
        #             FROM "account_move_line", account_account AS account, account_move AS am
        #             WHERE "account_move_line".partner_id IS NOT NULL
        #                 AND "account_move_line".account_id = account.id
        #                 AND am.state IN %s
        #                 AND "account_move_line".account_id IN %s
        #                 AND NOT account.deprecated
        #                 AND "account_move_line".reconciled = false"""
        # self.env.cr.execute(query, tuple(params))
        # partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        # partners = obj_partner.browse(partner_ids)
        # partners = sorted(partners, key=lambda x: (x.ref, x.name))
        # for partner in partners:
        #     print partner.name
        #     self._sum_partner(data, partner)




    def _sum_partner(self, data, partner):

        result = 0.0
        # query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '

        params = [partner.id,  tuple(data['computed']['account_ids'])]
        query = """
        SELECT partner_id,period_id,sum(credit),sum(debit)
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
