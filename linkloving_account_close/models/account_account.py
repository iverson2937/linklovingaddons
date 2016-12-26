# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    _description = "Account Account"

    debit = fields.Monetary(default=0.0, compute='_sum_debit_account')
    credit = fields.Monetary(default=0.0, compute='_sum_credit_account')
    balance = fields.Monetary(default=0.0,compute='_get_balance')
    @api.one
    def _get_balance(self):
        self.balance=self.debit-self.credit

    @api.one
    def _sum_debit_account(self):
        # if self.type == 'view':
        #     return self.debit
        cr = self._cr
        move_state = ['draft', 'posted']
        # if self.target_move == 'posted':
        #     move_state = ['posted','']
        cr.execute('SELECT sum(debit) \
                FROM account_move_line l \
                JOIN account_move am ON (am.id = l.move_id) \
                WHERE (l.account_id = %s) \
                AND (am.state IN %s) \
                 '
                   , (self.id, tuple(move_state)))
        sum_debit = cr.fetchone()[0] or 0.0
        self.debit=sum_debit

    @api.one
    def _sum_credit_account(self):
        cr = self._cr
        # if self.type == 'view':
        #     return self.credit
        move_state = ['draft', 'posted']
        # if self.target_move == 'posted':
        #     move_state = ['posted','']
        cr.execute('SELECT sum(credit) \
                FROM account_move_line l \
                JOIN account_move am ON (am.id = l.move_id) \
                WHERE (l.account_id = %s) \
                AND (am.state IN %s) \
        '
                   , (self.id, tuple(move_state)))
        sum_credit = cr.fetchone()[0] or 0.0
        # if self.init_balance:
        #     self.cr.execute('SELECT sum(credit) \
        #             FROM account_move_line l \
        #             JOIN account_move am ON (am.id = l.move_id) \
        #             WHERE (l.account_id = %s) \
        #             AND (am.state IN %s) \
        #             AND '+ self.init_query +' '
        #             ,(self.id, tuple(move_state)))
        #     # Add initial balance to the result
        #     sum_credit += self.cr.fetchone()[0] or 0.0
        self.credit=sum_credit
