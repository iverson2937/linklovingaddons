# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def get_default_period(self):
        """
        Return  default account period value
        """
        account_fiscalyear_obj = self.env['account.fiscalyear']
        ids = account_fiscalyear_obj.search([('state', '!=', 'done')])
        account_fiscalyear_id = False
        if ids:
            account_fiscalyear_id = ids[0]
        return account_fiscalyear_id

    fiscal_year_id = fields.Many2one('account.fiscalyear', default=get_default_period)


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

            if budget_id:
                sheet.budget_id = budget_id.id
