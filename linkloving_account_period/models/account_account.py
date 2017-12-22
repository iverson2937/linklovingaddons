# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo.addons import decimal_precision as dp


class AccountAccount(models.Model):
    _inherit = 'account.account'

    balance = fields.Float(compute='_compute', string='balance', digits=dp.get_precision('Payroll'))
    credit = fields.Float(compute='_compute', string='Credit', multi='balance')
    debit = fields.Float(compute='_compute', string='Debit')
    child_consol_ids = fields.Many2many('account.account', 'account_account_consol_rel', 'child_id', 'parent_id',
                                        'Consolidated Children')

    parent_id = fields.Many2one('account.account')
    child_parent_ids = fields.One2many('account.account', 'parent_id', 'Children')

    @api.multi
    def get_month_begin_balance(self):
        period_id = self.env['account.period'].get_current_period()
        for account in self:
            final = self.env['account.account.final'].search(
                [('account_id', '=', account.id), ('period_id', '=', period_id)])
            return final.start_debit - final.start_credit

    @api.multi
    def _get_children_and_consol(self):
        # this function search for all the children and all consolidated children (recursively) of the given account ids
        ids2 = self.search([('parent_id', 'child_of', self.id)])
        if ids2:
            ids2 = ids2.ids

        ids3 = []
        for child in self.child_consol_ids:
            ids3.append(child.id)
        if ids3:
            ids3 = self._get_children_and_consol(ids3)

        return ids2 + ids3

    @api.multi
    def _compute(self):
        """ compute the balance, debit and/or credit for the provided
        account ids
        Arguments:
        `ids`: account ids
        `field_names`: the fields to compute (a list of any of
                       'balance', 'debit' and 'credit')
        `arg`: unused fields.function stuff
        `query`: additional query filter (as a string)
        `query_params`: parameters for the provided query string
                        (__compute will handle their escaping) as a
                        tuple
        """
        cr = self._cr
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit",
            # by convention, foreign_balance is 0 when the account has no secondary currency, because the amounts may be in different currencies
            'foreign_balance': "(SELECT CASE WHEN currency_id IS NULL THEN 0 ELSE COALESCE(SUM(l.amount_currency), 0) END FROM account_account WHERE id IN (l.account_id)) as foreign_balance",
        }
        accounts = {}
        for account in self:
            credit = debit = balance = 0.0
            children_and_consolidated = account._get_children_and_consol()
            if children_and_consolidated:
                aml_query = self.env['account.move.line']._query_get()

                request = ("SELECT l.account_id as id, " + \
                           ', '.join(mapping.values()) +
                           " FROM account_move_line l" \
                           " WHERE l.account_id IN %s " \
                           " GROUP BY l.account_id")
                params = (tuple(children_and_consolidated),)
                print params, 'params'
                self.env.cr.execute(request, params)

                for row in cr.dictfetchall():
                    accounts[row['id']] = row

                # consolidate accounts with direct children
                children_and_consolidated.reverse()
                brs = list(self.browse(children_and_consolidated).ids)

                while brs:
                    current = brs.pop(0)
                    current_credit = accounts.get(current, {})
                    if current_credit:
                        credit = credit + current_credit.get('credit')
                        debit = debit + current_credit.get('debit')
                        balance = balance + current_credit.get('balance')
                account.credit = credit
                account.debit = debit
                account.balance = balance
