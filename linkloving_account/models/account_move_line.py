# -*- coding: utf-8 -*-

import time
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
from lxml import etree


# ----------------------------------------------------------
# Entries
# ----------------------------------------------------------


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    remark = fields.Text(related='payment_id.remark')
    amount1 = fields.Monetary(related='payment_id.amount')

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        # Perform all checks on lines
        company_ids = set()
        all_accounts = []
        partners = set()
        for line in self:
            company_ids.add(line.company_id.id)
            all_accounts.append(line.account_id)
            if (line.account_id.internal_type in ('receivable', 'payable')):
                partners.add(line.partner_id.id)
            if line.reconciled:
                raise UserError(_('You are trying to reconcile some entries that are already reconciled!'))
        if len(company_ids) > 1:
            raise UserError(_('To reconcile the entries company should be the same for all entries!'))
        if len(set(all_accounts)) > 1:
            raise UserError(_('Entries are not of the same account!'))
        if not all_accounts[0].reconcile:
            raise UserError \
                (_('The account %s (%s) is not marked as reconciliable !') % (
                    all_accounts[0].name, all_accounts[0].code))
        # 过渡账户
        if len(partners) > 2:
            raise UserError(_('The partner has to be the same on all lines for receivable and payable accounts!'))

        # reconcile everything that can be
        remaining_moves = self.auto_reconcile_lines()

        # if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
        if writeoff_acc_id and writeoff_journal_id and remaining_moves:
            all_aml_share_same_currency = all([x.currency_id == self[0].currency_id for x in self])
            writeoff_vals = {
                'account_id': writeoff_acc_id.id,
                'journal_id': writeoff_journal_id.id
            }
            if not all_aml_share_same_currency:
                writeoff_vals['amount_currency'] = False
            writeoff_to_reconcile = remaining_moves._create_writeoff(writeoff_vals)
            # add writeoff line to reconcile algo and finish the reconciliation
            remaining_moves = (remaining_moves + writeoff_to_reconcile).auto_reconcile_lines()
            return writeoff_to_reconcile
        return True

    amount = fields.Float(compute='_compute_amount')

    @api.multi
    def _compute_amount(self):
        for move in self:
            move.amount = move.debit if move.debit else move.credit * -1

    current_balance = fields.Float(string=u'当前余额')

    @api.multi
    def write(self, vals):
        res = super(AccountMoveLine, self).write(vals)
        if vals.get("state") == 'done':
            for move in self:
                if move and move.state:
                    if move.state == 'done':
                        move.current_balance = move.account_id.balance
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        for move in self:
            for line in move.line_ids:
                line.current_balance = line.account_id.balance

        return res
