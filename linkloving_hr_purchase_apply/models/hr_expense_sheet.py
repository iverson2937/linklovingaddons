# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    apply_line_ids = fields.One2many('hr.purchase.apply.line', 'sheet_id')
    balance = fields.Float(compute='_get_apply_balance')

    def _get_apply_balance(self):
        line_ids = self.env['hr.purchase.apply.line'].search(
            [('employee_id.user_id', '=', self.env.user.id), ('state', '=', 'approve'), ('sheet_id', '=', False)])
        self.balance = sum(line.sub_total for line in line_ids)

    @api.onchange('apply_line_ids')
    def on_change_apply_line_ids(self):
        expense_line_ids = self.expense_line_ids

        for line_id in self.apply_line_ids:
            result = self.env['hr.expense'].create({
                'product_id': line_id.product_id.id,
                'quantity': line_id.product_qty,
                'unit_amount': line_id.price_unit,
                'name': line_id.description
            })
            self.expense_line_ids = expense_line_ids + result
