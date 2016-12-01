# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    department_id = fields.Many2one('hr.department', string=u'部门')

    @api.depends('employee_id')
    def onchange_employee_id(self):
        self.department_id = self.employee_id.department_id


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    expense_no = fields.Char(string=u'报销编号')
    manager1_id = fields.Many2one('res.users')
    manager2_id = fields.Many2one('res.users')
    manager3_id = fields.Many2one('res.users')

    to_approve_id = fields.Many2one('res.users', readonly=True, track_visibility='onchange')



    @api.model
    def _compute_default_state(self):
        if self.user_has_groups('hr_expense.group_hr_expense_user'):
            state = 'manager2_approve'
        elif self.user_has_groups('hr_expense.group_hr_expense_manager'):
            state = 'manager3_approve'
        else:
            state = 'submit'
        return state

    state = fields.Selection([('submit', 'Submitted'),
                              ('manager1_approve', '主管审核'),
                              ('manager2_approve', '经理审核'),
                              ('manager3_approve', '总经理审核'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False,
                             default=_compute_default_state, required=True,
                             help='Expense Report State')

    @api.multi
    def manager1_approve(self):
        self.write({'state': 'manager2_approve', 'manager1_id': self.env.user.id})

    @api.multi
    def manager2_approve(self):
        self.write({'state': 'manager3_approve', 'manager2_id': self.env.user.id})

    @api.multi
    def manager3_approve(self):
        self.write({'state': 'approve', 'responsible_id': self.env.user.id})

    #
    # @api.multi
    # def manager2_approve(self):
    #     state = 'approve'
    #     if self.env.user.partner_id.department_id.parent_id:
    #         state = 'manager2_approve'
    #
    #     self.write({'state': state, 'manager1_id': self.env.user.id})

    @api.model
    def create(self, vals):
        if vals.get('expense_no', 'New') == 'New':
            vals['expense_no'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet') or '/'
            print vals['expense_no']
        exp = super(HrExpenseSheet, self).create(vals)
        if exp.employee_id == exp.employee_id.department_id.manager_id:
            exp.to_approve_id = exp.employee_id.department_id.parent_id.manager_id.user_id.id
        else:
            exp.to_approve_id = exp.employee_id.department_id.manager_id.user_id.id
        return exp
