# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'res.partner'

    employee_payment_id = fields.Many2one('account.account')
    payment_balance=fields.Monetary(compute='_credit_debit_get', string='Total Payable',
        help="Total amount you have to pay to this vendor.")

    @api.multi
    def _credit_debit_get(self):
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        where_params = [tuple(self.ids)] + where_params
        self._cr.execute("""SELECT l.partner_id, act.type, SUM(l.amount_residual)
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
                      LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                      WHERE act.type IN ('other')
                      AND l.partner_id IN %s
                      AND l.reconciled IS FALSE
                      """ + where_clause + """
                      GROUP BY l.partner_id, act.type
                      """, where_params)
        for pid, type, val in self._cr.fetchall():
            partner = self.browse(pid)
            partner.payment_balance = val



