# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    department_id = fields.Many2one('hr.department', string=u'部门')
    expense_no = fields.Char(string=u'报销编号')

    @api.depends('employee_id')
    def onchange_employee_id(self):
        self.department_id = self.employee_id.department_id

    @api.model
    def create(self, values):
        expense_no = values.get('expense_no')
        if not expense_no:
            values['expense_no'] = self.env['ir.sequence'].next_by_code('hr.expense') or '/'
        return super(HrExpense, self).create(values)

    @api.model
    def create(self, vals):
        if vals.get('expense_no', 'New') == 'New':
            vals['expense_no'] = self.env['ir.sequence'].next_by_code('hr.expense') or '/'
        return super(HrExpense, self).create(vals)
