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

    def get_current_fiscalyear(self):
        account_fiscal_obj = self.env['account.fiscalyear']
        ids = account_fiscal_obj.search([('state', '!=', 'done')])
        fiscal_id = ids[0]
        return fiscal_id

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
        self.state = 'done'


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

    def reopen_period(self):
        self.state = 'open'

    def get_current_period(self):

        account_period_obj = self.env['account.period']
        ids = account_period_obj.search([('state', '!=', 'done')])
        period_id = ids[0]
        return period_id.id

    def _get_next_period(self):
        account_period_obj = self.env['account.period']
        ids = account_period_obj.search([('state', '!=', 'done')])
        period_id = False
        if len(ids) == 1:
            raise UserError(u'已经没有未关闭的会计区间，请建立新的财年和会计区间！')
        period_id = ids[1]
        return period_id

    @api.multi
    def unlink(self):
        for period in self:
            if period.env['account.move.line'].search([('period_id', '=', period.id)]):
                raise UserError(u'此会计区间已经有分录生产，不可以删除')
        return super(AccountPeriod, self).unlink()

    def _get_account_period_accounts(self, accounts, period_id):
        """ compute the balance, debit and credit for the provided accounts and period
            :Arguments:
                `accounts`: list of accounts record,
                `period_id`: it's used to display which period account data
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        # compute the balance, debit and credit for the provided accounts
        request = (
            "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
            " FROM " + "account_move_line" + " WHERE account_id IN %s  "
            + " AND period_id = %s "
            + "GROUP BY account_id"

        )
        params = (tuple(accounts.ids), str(period_id))
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            print row
            account_result[row.pop('id')] = row
        print account_result
        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            res['id'] = account.id
            if account.id in account_result.keys():
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
                account_res.append(res)
        return account_res

    def _sum_partner(self, account_ids, partner):

        result = 0.0
        # query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '

        params = [partner.id, tuple(account_ids)]
        query = """
        SELECT account_id,sum(credit),sum(debit)
                FROM "account_move_line"
                WHERE "account_move_line".partner_id = %s
                    AND account_id IN %s
                    GROUP BY account_id
                    """
        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()

        return contemp

    @api.multi
    def close_period(self):

        accounts = self.env['account.account'].search([])
        account_res = self._get_account_period_accounts(accounts, self.id)
        final_obj = self.env['account.account.final']
        account_datas = {}
        # 本期发生的借贷
        for account in account_res:
            account_datas.update({
                account['id']: {
                    'credit': account['credit'],
                    'debit': account['debit']
                }
            })
        for account in self.env['account.account'].search([('deprecated', '=', False)]):
            credit = debit = 0
            if account_datas.get(account.id):
                credit = account_datas[account.id]['credit']
                debit = account_datas[account.id]['debit']
            vals = {
                'credit': credit,
                'debit': debit,
                'end_credit': account.credit,
                'end_debit': account.debit,
                'period_id': self.id,
                'account_id': account.id,
            }
            period_data = final_obj.search(
                [('account_id', '=', account['id']), ('partner_id', '=', False), ('period_id', '=', self.id)])
            # self.state = 'done'
            if not period_data:
                # 系统第一个会计区间没有数据
                final_obj.create(vals)
            else:
                period_data.write({
                    # 'end_credit': period_data.start_credit + credit,
                    # 'end_debit': period_data.start_debit + debit,
                    'end_credit': account.credit,
                    'end_debit': account.debit,
                    'credit': credit,
                    'debit': debit
                })
            # 建立新的会计区间初始数据
            period_id = self._get_next_period()
            next_period_data = final_obj.search(
                [('account_id', '=', account['id']), ('partner_id', '=', False),
                 ('period_id', '=', period_id.id)])
            if not next_period_data:
                final_obj.create({
                    'period_id': period_id.id,
                    'account_id': account['id'],
                    'start_credit': account.credit,
                    'start_debit': account.debit
                })
            next_period_data.write({
                # 'start_credit': period_data.start_credit + credit,
                # 'start_debit': period_data.start_debit + debit
                'start_credit': account.credit,
                'start_debit': account.debit
            })

        # 获取每个业务伙伴的应收应付汇总
        obj_partner = self.env['res.partner']

        move_state = ['posted']

        self.env.cr.execute("""
                            SELECT a.id
                            FROM account_account a
                            WHERE a.internal_type IN %s
                            AND NOT a.deprecated""", (tuple(['payable', 'receivable']),))
        account_ids = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(move_state), tuple(account_ids)]
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
        period_id = self._get_next_period()
        for partner in partners:

            account_id, credit, debit = self._sum_partner(account_ids, partner)
            period_partner_data = final_obj.search(
                [('account_id', '=', account_id), ('period_id', '=', self.id), ('partner_id', '=', partner.id)])
            if not period_partner_data:
                final_obj.create({
                    'period_id': self.id,
                    'partner_id': partner.id,
                    'account_id': account_id,
                    'credit': credit,
                    'debit': debit,
                    'end_credit': credit,
                    'end_debit': debit
                })
            else:
                period_partner_data.write({'credit': credit,
                                           'debit': debit,
                                           'end_credit': period_partner_data.start_credit,
                                           'end_debit': period_partner_data.start_debit})
                # final_obj.create({
                #     'period_id': period_id.id,
                #     'partner_id': partner.id,
                #     'account_id': account_id,
                #     'start_credit': credit + period_partner_data.start_credit,
                #     'start_debit': debit + period_partner_data.start_debit
                # })
        self.state = 'done'
