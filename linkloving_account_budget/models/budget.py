# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountBudget(models.Model):
    _name = 'linkloving.account.budget'
    _order = 'create_date desc'
    name = fields.Char(string='名称')
    department_id = fields.Many2one('hr.department', string=u'部门')
    total_employee = fields.Integer(related='department_id.total_employee', string='实际人数')
    # team_id = fields.Many2one('crm.team', related='department_id.team_id')
    amount = fields.Float(string=u'预算总金额', compute='get_budget_balance')
    amount_used = fields.Float(string=u'已使用金额', compute='get_budget_balance')
    balance = fields.Float(string=u'预算余额', compute='get_budget_balance')
    description = fields.Text(string=u'描述')
    is_create_line = fields.Boolean(default=False)
    sale_target = fields.Float(string=u'销售目标')

    def _get_fiscal_year_id(self):
        fiscal_year_id = self.env['account.fiscalyear'].search([('state', '!=', 'done')], limit=1)
        return fiscal_year_id.id

    @api.model
    def get_department_budget_report(self, **kwargs):
        products = self.env['product.product'].search([('can_be_expensed', '=', True)])
        departments = self.env['hr.department'].search([('has_budget', '=', True)])
        BudgetLine = self.env['linkloving.account.budget.line']
        Budget = self.env['linkloving.account.budget']
        res = []
        for department in departments:
            budget = Budget.search([('department_id', '=', department.id)])

            manpower = budget.man_power
            product_dict = {'department_id': department.name, 'manpower': manpower,
                            'sale_target': budget.sale_target if budget.sale_target else 0,
                            'sale_expense_rate': str(
                                round(budget.amount / budget.sale_target, 4) * 100) + "%" if budget.sale_target else '',
                            'sub_total': budget.amount}
            for product in products:
                lines = BudgetLine.search([('product_id', '=', product.id), ('department_id', '=', department.id)])
                amount = sum(line.amount for line in lines)
                product_dict.update({
                    product.default_code: amount,
                })
            res.append(product_dict)
        print len(res)

        return res

    fiscal_year_id = fields.Many2one('account.fiscalyear', string='年度', default=_get_fiscal_year_id)
    line_ids = fields.One2many('linkloving.account.budget.line', 'budget_id')
    man_power = fields.Integer(string='预算人数')
    state = fields.Selection([
        ('draft', '草稿'),
        ('done', '正式'),
    ], default='draft')

    _sql_constraints = [
        ('name_company_uniq', 'unique(department_id, fiscal_year_id)', '每个部门费用类别只可以每年只可以做一次预算'),
    ]

    @api.constrains('line_ids')
    def _check_product_recursion(self):
        for budget in self:
            product_ids = budget.line_ids.mapped('product_id')
            if len(product_ids) != len(budget.line_ids):
                raise UserError('明细不可以重复')

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

    @api.multi
    def create_budget_line(self):
        line_obj = self.env['linkloving.account.budget.line']
        products = self.env['product.product'].search([('can_be_expensed', '=', True)])
        for budget in self:
            for product in products:
                if product.id not in budget.line_ids.mapped('product_id').ids:
                    line_obj.create({
                        'budget_id': budget.id,
                        'product_id': product.id,
                        'fiscal_year_id': budget.fiscal_year_id.id
                    })
            # budget.is_create_line = True

        return True


class AccountBudgetLine(models.Model):
    _name = 'linkloving.account.budget.line'
    _order = 'create_date desc'
    budget_id = fields.Many2one('linkloving.account.budget', on_delete="cascade")
    department_id = fields.Many2one('hr.department', string=u'部门', related='budget_id.department_id')
    product_id = fields.Many2one('product.product', string=u'费用类别', domain=[('can_be_expensed', '=', True)])
    amount = fields.Float(string=u'预算金额')
    amount_used = fields.Float(string=u'已使用金额', compute='get_budget_balance')
    balance = fields.Float(string=u'预算余额', compute='get_budget_balance')
    expense_ids = fields.One2many('hr.expense', 'budget_id', domain=[('state', '=', 'done')])
    description = fields.Text(string=u'描述')
    fiscal_year_id = fields.Many2one('account.fiscalyear', string='年度')
    expense_len = fields.Integer(compute='_compute_expense_len', string=' ')

    @api.multi
    def _compute_expense_len(self):
        for line in self:
            line.expense_len = len(line.expense_ids)

    state = fields.Selection([
        ('draft', '草稿'),
        ('done', '正式'),
    ], related='budget_id.state')

    _sql_constraints = [
        ('name_company_uniq', 'unique(department_id, fiscal_year_id, product_id)', '每个部门费用类别只可以每年只可以做一次预算'),
    ]

    @api.multi
    def get_budget_balance(self):
        for budget in self:
            budget.amount_used = sum(expense.total_amount for expense in budget.expense_ids)
            budget.balance = budget.amount - budget.amount_used

    def check_expense_detail(self):
        return {
            'name': u'费用明细',
            'res_model': 'hr.expense',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.expense_ids.ids)],
            'view_mode': 'tree,form',
        }
