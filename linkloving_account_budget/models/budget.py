# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountBudget(models.Model):
    _name = 'linkloving.account.budget'
    _order = 'create_date desc'
    name = fields.Char(string='名称')
    department_id = fields.Many2one('hr.department', string=u'部门')
    product_id = fields.Many2one('product.product', string=u'费用类别', domain=[('can_be_expensed', '=', True)])
    amount = fields.Float(string=u'预算总金额')
    balance = fields.Float(string=u'预算余额', compute='get_budget_balance')
    sheet_ids = fields.One2many('hr.expense.sheet', 'budget_id')
    description = fields.Text(string=u'描述')
    fiscal_year_id = fields.Many2one('account.fiscalyear', string='年度')
    state = fields.Selection([
        ('draft', '草稿'),
        ('done', '正式'),
    ], default='draft')

    _sql_constraints = [
        ('name_company_uniq', 'unique(department_id, fiscal_year_id, product_id)', '每个部门费用类别只可以每年只可以做一次预算'),
    ]

    @api.multi
    def unlink(self):
        for budget in self:
            if budget.state == 'formal':
                raise UserError('不能删除')
        return super(AccountBudget, self).unlink()

    def set_to_done(self):
        self.state = 'done'

    @api.multi
    def get_budget_balance(self):
        for budget in self:
            budget.balance = budget.amount - sum(sheet.total_amount for sheet in budget.sheet_ids)
