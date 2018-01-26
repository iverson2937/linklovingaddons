# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountBudget(models.Model):
    _name = 'linkloving.account.budget'
    _order = 'create_date desc'
    name = fields.Char(string='名称')
    department_id = fields.Many2one('hr.department', string=u'部门')
    amount = fields.Float(string=u'预算总金额', compute='get_budget_balance')
    amount_used = fields.Float(string=u'已使用金额', compute='get_budget_balance')
    balance = fields.Float(string=u'预算余额', compute='get_budget_balance')
    description = fields.Text(string=u'描述')
    fiscal_year_id = fields.Many2one('account.fiscalyear', string='年度')
    line_ids = fields.One2many('linkloving.account.budget.line', 'budget_id')
    state = fields.Selection([
        ('draft', '草稿'),
        ('done', '正式'),
    ], default='draft')

    _sql_constraints = [
        ('name_company_uniq', 'unique(department_id, fiscal_year_id)', '每个部门费用类别只可以每年只可以做一次预算'),
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
            budget.balance = sum(line.balance for line in budget.line_ids)
            budget.amount = sum(line.amount for line in budget.line_ids)
            budget.amount_used = sum(line.amount_used for line in budget.line_ids)


class AccountBudgetLine(models.Model):
    _name = 'linkloving.account.budget.line'
    _order = 'create_date desc'
    budget_id = fields.Many2one('linkloving.account.budget', on_delete="cascade")
    department_id = fields.Many2one('hr.department', string=u'部门', related='budget_id.department_id')
    product_id = fields.Many2one('product.product', string=u'费用类别', domain=[('can_be_expensed', '=', True)])
    amount = fields.Float(string=u'预算金额')
    amount_used = fields.Float(string=u'已使用金额', compute='get_budget_balance')
    balance = fields.Float(string=u'预算余额', compute='get_budget_balance')
    expense_ids = fields.One2many('hr.expense', 'budget_id')
    description = fields.Text(string=u'描述')
    fiscal_year_id = fields.Many2one('account.fiscalyear', string='年度')
    state = fields.Selection([
        ('draft', '草稿'),
        ('done', '正式'),
    ], related='budget_id.state')

    _sql_constraints = [
        ('name_company_uniq', 'unique(department_id, fiscal_year_id, product_id)', '每个部门费用类别只可以每年只可以做一次预算'),
    ]

    @api.multi
    def unlink(self):
        for budget in self:
            if budget.state == 'formal':
                raise UserError('不能删除')
        return super(AccountBudget, self).unlink()

    @api.multi
    def get_budget_balance(self):
        for budget in self:
            budget.amount_used = sum(expense.total_amount for expense in budget.expense_ids)
            budget.balance = budget.amount - budget.amount_used
