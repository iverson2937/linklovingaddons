# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    expense_no = fields.Char(string=u'报销编号')
    approve_ids = fields.Many2many('res.users')
    is_deduct_payment = fields.Boolean(default=False)
    deduct_amount = fields.Float()
    pre_payment_reminding = fields.Float(string=u'暂支余额', related='employee_id.pre_payment_reminding')
    payment_id = fields.Many2one('account.employee.payment')
    income = fields.Boolean()
    partner_id = fields.Many2one('res.partner')

    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        res = self.mapped('expense_line_ids').action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and self.pre_payment_reminding >= self.total_amount:
            self.write({'state': 'done'})
        else:
            self.write({'state': 'post'})
        return res

    # FIXME:USE BETTER WAY TO HIDE THE BUTTON
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
        if not department:
            UserError(u'请设置该员工部门')
        if not department.manager_id:
            UserError(u'该员工所在部门未设置经理(审核人)')
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
        self.to_approve_id = False

        self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.model
    def create(self, vals):
        if vals.get('expense_no', 'New') == 'New':
            vals['expense_no'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet') or '/'
        exp = super(HrExpenseSheet, self).create(vals)
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

    @api.multi
    def deduct_payment(self, payment_id):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))
        vals = {}
        if self.pre_payment_reminding >= self.total_amount:

            vals.update({'state': 'done', 'deduct_amount': self.total_amount})
        else:
            vals.update({'state': 'post', 'deduct_amount': self.pre_payment_reminding})
        vals.update({'is_deduct_payment': True, 'payment_id': payment_id})
        self.write(vals)

        self.mapped('expense_line_ids').action_move_create()

    @api.multi
    def no_deduct_payment(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        res = self.mapped('expense_line_ids').action_move_create()
        self.write({'state': 'post'})
        return res

    @api.multi
    def to_do_journal_entry(self):
        # 如果由公司字付，直接产生分录，状态变为完成
        if self.payment_mode == 'company_account':
            self.mapped('expense_line_ids').action_move_create()
            self.write({'state': 'done'})
            return
        # 如果没有暂支余额
        if not self.pre_payment_reminding:
            if any(sheet.state != 'approve' for sheet in self):
                raise UserError(_("You can only generate accounting entry for approved expense(s)."))

            if any(not sheet.journal_id for sheet in self):
                raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

            self.mapped('expense_line_ids').action_move_create()
            self.write({'state': 'post'})
        else:
            return {
                'name': _('费用报销'),
                'type': 'ir.actions.act_window',
                'res_model': "account.employee.payable.wizard",
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_employee_id': self.employee_id.id},
                'target': 'new'
            }

    @api.multi
    def register_payment_action(self):
        amount = self.total_amount
        if self.is_deduct_payment:
            amount = self.total_amount - self.deduct_amount

        context = {'default_payment_type': 'outbound', 'default_amount': amount}

        return {
            'name': _('Send Money'),
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': False,
            'res_model': 'hr.expense.register.payment.wizard',
            'domain': [],
            'context': dict(context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def action_receive_payment(self):
        amount = self.total_amount
        account_id = self.expense_line_ids.product_id.property_account_income_id
        if not account_id:
            raise UserError('请设置产品的收入科目')

        context = {'default_payment_type': 'inbound', 'default_amount': amount,
                   'default_partner_id': self.partner_id.id, 'default_account_id': account_id.id}

        return {
            'name': _('收钱'),
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': False,
            'res_model': 'hr.expense.receive.wizard',
            'domain': [],
            'context': dict(context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        if self._context.get('to_approve_id'):
            return [('to_approve_id', '=', self.env.user.id)]
        if self._context.get('search_default_to_post'):
            return [('state', '=', 'approve')]
        if self._context.get('search_default_approved'):
            return [('state', '=', 'post')]
