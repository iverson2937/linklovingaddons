# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountCustomTax(models.Model):
    _name = 'account.custom.tax'

    state = fields.Selection([
        ('draft', '草稿'),
        ('done', '完成'),
    ], default='draft')
    date = fields.Date(default=fields.Date.context_today)
    amount = fields.Float(string='金额')
    rate = fields.Float(string='税率', default=0.17)
    tax_amount = fields.Float(string='税金金额', compute='get_tax_amount')

    _sql_constraints = [
        ('positive_amount', 'CHECK(amount>0.0)', '金额必须大于0'),
    ]

    @api.multi
    def unlink(self):
        for r in self:
            if r.state == 'done':
                raise UserError('不可以删除已经完成的单据')
            return super(AccountCustomTax, self).unlink()

    @api.multi
    def get_tax_amount(self):
        for r in self:
            r.tax_amount = (r.amount / (1 + r.rate)) * r.rate

    move_id = fields.Many2one('account.move')

    @api.multi
    def action_open_journal_entries(self):
        res = self.env['ir.actions.act_window'].for_xml_id('account', 'action_move_journal_line')
        # DO NOT FORWARD-PORT
        res['domain'] = [('id', '=', self.move_id.id)]
        res['context'] = {}
        return res


    def confirm(self):

        debit_line_vals = {
            'name': u'自开票',
            'debit': self.tax_amount,
            'account_id': self.env['account.account'].search([('code', 'ilike', '9999')]).id
        }
        credit_line_vals = {
            'name': u'自开票',
            'credit': self.tax_amount,
            'account_id': self.env.ref('linkloving_account_tax.custom_tax').id
        }
        move = self.env['account.move'].create({
            'journal_id': 1,
            'line_ids': [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        })
        move.post()
        self.move_id = move.id

        self.state = 'done'
