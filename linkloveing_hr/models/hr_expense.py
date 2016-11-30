# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    department_id = fields.Many2one('hr.department', string=u'部门')


    @api.depends('employee_id')
    def onchange_employee_id(self):
        self.department_id = self.employee_id.department_id


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    expense_no = fields.Char(string=u'报销编号')

    @api.model
    def create(self, vals):
        if vals.get('expense_no', 'New') == 'New':
            vals['expense_no'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet') or '/'
            print vals['expense_no']
        return super(HrExpenseSheet, self).create(vals)
