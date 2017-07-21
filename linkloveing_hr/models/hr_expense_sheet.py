# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    _rec_name = 'expense_no'

    @api.depends('expense_line_ids')
    def _get_full_name(self):
        name = ''
        for line in self.expense_line_ids:
            name += line.name + ' ;'
        self.name = name

    name = fields.Char(compute='_get_full_name', store=True, required=False)
    expense_no = fields.Char(default=lambda self: _('New'))
    approve_ids = fields.Many2many('res.users')
    is_deduct_payment = fields.Boolean(default=False)
    pre_payment_reminding = fields.Float(related='employee_id.pre_payment_reminding')
    payment_id = fields.Many2one('account.employee.payment')
    income = fields.Boolean(default=False)
    partner_id = fields.Many2one('res.partner')
    payment_line_ids = fields.One2many('account.employee.payment.line', 'sheet_id')
    remark_comments_ids = fields.One2many('hr.remark.comment', 'expense_sheet_id', string=u'审核记录')

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

    state = fields.Selection([('draft', u'草稿'),
                              ('submit', 'Submitted'),
                              ('manager1_approve', u'1级审核'),
                              ('manager2_approve', u'2级审核'),
                              ('manager3_approve', 'General Manager Approved'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False,
                             default='draft', required=True,
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
        # 如果没有上级部门，或者报销金额小于该部门的允许最大金额
        if not department.parent_id or (department.allow_amount and self.total_amount < department.allow_amount):
            self.to_approve_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})
        else:
            if not department.parent_id.manager_id:
                raise UserError(u'上级部门没有设置经理,请联系管理员')
            self.to_approve_id = department.parent_id.manager_id.user_id.id
            self.write({'state': 'manager1_approve', 'approve_ids': [(4, self.env.user.id)]})

        create_remark_comment(self, u'1级审核')

    @api.multi
    def manager2_approve(self):

        department = self.to_approve_id.employee_ids.department_id
        if not department.parent_id or (department.allow_amount and self.total_amount < department.allow_amount):
            self.to_approve_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

        else:
            if not department.parent_id.manager_id:
                raise UserError(u'上级部门没有设置经理,请联系管理员')
            self.to_approve_id = department.parent_id.manager_id.user_id.id

            self.write({'state': 'manager2_approve', 'approve_ids': [(4, self.env.user.id)]})

        create_remark_comment(self, u'2级审核')

    @api.multi
    def set_account_date(self):
        sheet_ids = self.env['hr.expense.sheet'].search([('state', '=', 'done'), ('accounting_date', '=', False)])
        for sheet in sheet_ids:
            sheet.accounting_date = sheet.write_date

    @api.multi
    def hr_expense_sheet_post(self):
        for exp in self:
            if not exp.expense_line_ids:
                raise UserError(u'请填写报销明细')
            state = 'submit'
            department = exp.department_id
            if exp.employee_id == department.manager_id:

                if not department.parent_id or (
                            department.allow_amount and self.total_amount > department.allow_amount):
                    state = 'approve'
                    exp.write({'state': 'approve'})
                else:
                    if not department.parent_id.manager_id:
                        raise UserError(u'上级部门未设置审核人')
                    exp.to_approve_id = department.parent_id.manager_id.user_id.id
            else:
                # if not department.parent_id.manager_id:
                #     raise UserError(u'上级部门没有设置经理,请联系管理员')
                if not department.manager_id:
                    raise UserError(u'请设置部门审核人')
                exp.to_approve_id = department.manager_id.user_id.id
            exp.write({'state': state})
            create_remark_comment(exp, u'送审')

    @api.multi
    def manager3_approve(self):
        self.to_approve_id = False

        self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.multi
    def return_to_approve(self):
        self.state = 'approve'

    @api.model
    def create(self, vals):
        if vals.get('expense_no', 'New') == 'New':
            if self._context.get('default_income'):
                vals['expense_no'] = self.env['ir.sequence'].next_by_code('account.income') or '/'
            else:
                vals['expense_no'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet') or '/'

        exp = super(HrExpenseSheet, self).create(vals)
        #

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

        create_remark_comment(self, u'重新提交')

        return self.write({'state': 'submit'})

    @api.multi
    def process(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        res = self.mapped('expense_line_ids').action_move_create()
        self.write({'state': 'post'})
        if not self.accounting_date:
            self.accounting_date = fields.date.today()
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
                'name': _('Expense Sheet'),
                'type': 'ir.actions.act_window',
                'res_model': "account.employee.payable.wizard",
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_employee_id': self.employee_id.id},
                'target': 'new'
            }

    @api.multi
    def register_payment_action(self):

        amount = self.total_amount - sum(line.amount for line in self.payment_line_ids)

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
            'name': _('Receivable Payment'),
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


def create_remark_comment(data, body):
    values = {
        'body': body,
        'message_type': data.state,
        'target_uid': data.to_approve_id.id,
        'employee_payment_id' if data._name == 'account.employee.payment' else 'expense_sheet_id': data.id
    }
    return data.env['hr.remark.comment'].create(values)


class HrRemarkComment(models.Model):
    _name = 'hr.remark.comment'

    body = fields.Char(string=u'内容')
    target_uid = fields.Many2one('res.users')

    message_type = fields.Selection([
        ('draft', u'草稿'),
        ('submit', u'送审'),
        ('manager1_approve', u'1级审核'),
        ('manager2_approve', u'2级审核'),
        ('done', u'审核通过'),
        ('refuse', u'拒绝'),
        ('update', u'修改'),
        ('manager3_approve', u'3级审核'),
        ('approve', u'批准'),
        ('post', 'Posted'),
        ('cancel', u'拒绝'),
        ('confirm', u'Confirm'),
        ('paid', u'Paid'),
    ], default='draft')
    expense_sheet_id = fields.Many2one('hr.expense.sheet', string=u'审核对象')
    employee_payment_id = fields.Many2one('account.employee.payment', string=u'暂支审核对象')


class HrExpenseRefuseWizard(models.TransientModel):
    _inherit = "hr.expense.refuse.wizard"

    @api.multi
    def expense_refuse_reason(self):
        self.ensure_one()

        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)
        expense_sheet.refuse_expenses(self.description)
        create_remark_comment(expense_sheet, u'拒绝')
        return {'type': 'ir.actions.act_window_close'}


class HrResUsers(models.Model):
    _inherit = "res.users"

    remark_ids = fields.One2many('hr.remark.comment', 'target_uid')
