# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    fiscal_year_id = fields.Many2one('account.fiscalyear')


class HrExpense(models.Model):
    _inherit = 'hr.expense'
    fiscal_year_id = fields.Many2one('account.fiscalyear', related='sheet_id.fiscal_year_id')
    budget_id = fields.Many2one('linkloving.account.budget.line', compute='get_budget_id')


    @api.multi
    def get_budget_id(self):
        for sheet in self:
            budget_id = self.env['linkloving.account.budget.line'].search(
                [('fiscal_year_id', '=', sheet.fiscal_year_id.id), ('department_id', '=', sheet.department_id.id),
                 ('product_id', '=', sheet.product_id.id)])
            #
            # if budget_id:
            #     sheet.budget_id = budget_id.id
