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
    approve_ids = fields.Many2many('res.users')
    pre_payment_reminding = fields.Float(string=u'暂支余额')

    def _get_is_show(self):
        if self._context.get('uid') == self.to_approve_id.id:
            self.is_show = True
        else:
            self.is_show = False

    is_show = fields.Boolean(compute=_get_is_show)

    to_approve_id = fields.Many2one('res.users', readonly=True, track_visibility='onchange')

    state = fields.Selection([('submit', 'Submitted'),
                              ('manager1_approve', '一级审核'),
                              ('manager2_approve', '二级审核'),
                              ('manager3_approve', '总经理审核'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False,
                             default='submit', required=True,
                             help='Expense Report State')

    @api.multi
    def manager1_approve(self):
        # if self.employee_id == self.employee_id.department_id.manager_id:
        #     self.to_approve_id = self.employee_id.department_id.parent_id.manager_id.user_id.id
        # else:
        department = self.to_approve_id.employee_ids.department_id
        if department.allow_amount and self.total_amount < department.allow_amount:
            self.to_approve_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

        else:
            self.to_approve_id = department.parent_id.manager_id.user_id.id

            self.write({'state': 'manager1_approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.multi
    def manager2_approve(self):
        department = self.to_approve_id.employee_ids.department_id
        if department.allow_amount and self.total_amount < department.allow_amount:
            self.to_approve_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

        else:
            self.to_approve_id = department.parent_id.manager_id.user_id.id

            self.write({'state': 'manager2_approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.multi
    def manager3_approve(self):

        self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

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
        exp.pre_payment_reminding = -exp.employee_id.user_id.partner_id.debit
        if exp.employee_id == exp.employee_id.department_id.manager_id:
            department = exp.to_approve_id.employee_ids.department_id
            if department.allow_amount and self.total_amount > department.allow_amount:
                exp.write({'state': 'approve'})
            else:
                exp.to_approve_id = exp.employee_id.department_id.parent_id.manager_id.user_id.id
        else:
            exp.to_approve_id = exp.employee_id.department_id.manager_id.user_id.id
        return exp

    @api.multi
    def write(self, vals):
        if vals.get('state') == 'cancel':
            self.to_approve_id = False
        return super(HrExpenseSheet, self).write(vals)

    @api.multi
    def reset_expense_sheets(self):
        if self.employee_id == self.employee_id.department_id.manager_id:
            department = self.to_approve_id.employee_ids.department_id
            if department.allow_amount and self.total_amount > department.allow_amount:
                self.write({'state': 'approve'})
            else:
                self.to_approve_id = self.employee_id.department_id.parent_id.manager_id.user_id.id
        else:
            self.to_approve_id = self.employee_id.department_id.manager_id.user_id.id

        return self.write({'state': 'submit'})
