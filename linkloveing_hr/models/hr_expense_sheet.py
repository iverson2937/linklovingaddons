# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import jpush
from JPush import JPushExtend


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    _rec_name = 'expense_no'

    default_payment_ids = fields.One2many('account.employee.payment', compute="_get_default_payment_ids")

    related_payment_ids = fields.Many2many('account.employee.payment', 'payment_sheet_rel', 'sheet_id', 'payment_id')

    @api.multi
    def get_formview_id(self):
        """ Update form view id of action to open the invoice """
        if self._context.get('show_custom_form'):
            return self.env.ref('linkloveing_hr.hr_expense_sheet_payment').id
        return super(HrExpenseSheet, self).get_formview_id()

    @api.multi
    def _get_default_payment_ids(self):
        for sheet in self:
            payment_ids = self.env['account.employee.payment'].search(
                [('can_return', '=', True), ('employee_id', '=', sheet.employee_id.id)])
            ids = []
            amount = sheet.total_amount
            for payment in payment_ids:
                if payment.pre_payment_reminding >= amount:
                    amount = payment.pre_payment_reminding - amount
                    ids.append(payment.id)
                    break
            print ids, 'ids'
            sheet.default_payment_ids = ids

    @api.multi
    def _get_payment_info_JSON(self):
        for sheet in self:
            value = {
                'pre_payment_amount': sheet.pre_payment_reminding,
                'payment_line_amount': sheet.payment_line_amount,
                'employee_id': sheet.employee_id.id,
                'payment_ids': sheet.default_payment_ids.ids,
                'sheet_id': sheet.id,
            }
            sheet.to_deduct_payment = json.dumps(value)

    to_deduct_payment = fields.Char(compute=_get_payment_info_JSON)

    sheet_type = fields.Selection([
        ('normal', '普通报销'),
        ('purchase', '申购报销'),
    ], default='normal')

    @api.depends('expense_line_ids')
    def _get_full_name(self):
        name = ''
        for line in self.expense_line_ids:
            name += line.name + ' ;'
        self.name = name

    name = fields.Char(compute='_get_full_name', store=True, required=False)
    account_payment_ids = fields.One2many('account.payment', 'res_id', domain=[('res_model', '=', 'hr.expense.sheet')])
    expense_no = fields.Char(default=lambda self: _('New'))
    approve_ids = fields.Many2many('res.users')
    is_deduct_payment = fields.Selection([
        (1, '是'),
        (0, '否')
    ])

    pre_payment_reminding = fields.Float(related='employee_id.pre_payment_reminding')
    product_id = fields.Many2one(related='expense_line_ids.product_id')
    account_id = fields.Many2one(related='expense_line_ids.account_id')
    payment_id = fields.Many2one('account.employee.payment')
    income = fields.Boolean(default=False)
    partner_id = fields.Many2one('res.partner')
    # 抵扣明细行
    account_payment_line_ids = fields.One2many('account.employee.payment.line', 'sheet_id')
    remark_comments_ids = fields.One2many('hr.remark.comment', 'expense_sheet_id', string=u'审核记录')
    department_id = fields.Many2one('hr.department', string='Department',
                                    states={'post': [('readonly', True)], 'done': [('readonly', False)]})

    reject_reason = fields.Char(string=u'拒绝原因')
    has_payment_line_ids = fields.Boolean(compute='_compute_has_payment_line_ids')
    payment_line_amount = fields.Float(string=u'暂支抵扣金额', compute='_compute_has_payment_line_ids')
    has_payment_ids = fields.Boolean(compute='_compute_has_payment_ids')

    @api.multi
    def action_cancel(self):
        for sheet in self:
            # 取消过账分录
            if sheet.account_move_id:
                sheet.account_move_id.button_cancel()
                sheet.account_move_id.unlink()
            # 取消暂支抵扣
            sheet.cancel_deduct_payment()
            # 取消付款分录
            if sheet.account_payment_ids:
                for payment in sheet.account_payment_ids:
                    payment.cancel()
                    payment.unlink()

            sheet.state = 'approve'

    @api.multi
    def _compute_has_payment_ids(self):
        for sheet in self:

            if sheet.account_payment_ids:
                sheet.has_payment_ids = True
            else:
                sheet.has_payment_ids = False

    @api.multi
    def _compute_has_payment_line_ids(self):
        for sheet in self:
            if sheet.account_payment_line_ids:
                sheet.has_payment_line_ids = True
                sheet.payment_line_amount = sum(line.amount for line in sheet.account_payment_line_ids)
            else:
                sheet.has_payment_line_ids = False

    @api.onchange('department_id')
    def _onchange_department_id(self):
        for line in self.expense_line_ids:
            line.department_id = line.sheet_id.department_id.id

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

    @api.multi
    def _get_is_show(self):
        for sheet in self:
            if sheet.to_approve_id and self.env.uid == self.to_approve_id.id:
                sheet.is_show = True
            else:
                sheet.is_show = False

    is_show = fields.Boolean(compute=_get_is_show)

    @api.multi
    def cancel_deduct_payment(self):
        for sheet in self:
            if sheet.account_payment_line_ids:
                for line in sheet.account_payment_line_ids:
                    line.unlink()

    to_approve_department_id = fields.Many2one('hr.department', readonly=True, string=u'待审核部门',
                                               compute='_get_to_approve_department', store=True)

    @api.multi
    def _get_to_approve_department(self):
        for sheet in self:
            if sheet.to_approve_id:
                sheet.to_approve_department_id = sheet.to_approve_id.employee_ids[0].department_id.id

    to_approve_id = fields.Many2one('res.users', compute='_get_to_approve_id', store=True)

    @api.multi
    @api.depends('to_approve_department_id', 'to_approve_department_id.manager_id')
    def _get_to_approve_id(self):

        for sheet in self:
            if sheet.to_approve_department_id:
                sheet.to_approve_id = sheet.to_approve_department_id.manager_id.sudo().user_id

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
        department = self.to_approve_department_id
        if self.state == 'approve':
            return
        state = 'manager1_approve'
        # 如果没有上级部门，或者报销金额小于该部门的允许最大金额
        to_approve_department_id = department.get_to_approve_department(self.env.user.employee_ids[0])
        if not to_approve_department_id or (department.allow_amount and self.total_amount < department.allow_amount):
            state = 'approve'
            to_approve_department_id = False
        self.write({
            'state': state,
            'approve_ids': [(4, self.env.user.id)],
            'to_approve_department_id': to_approve_department_id
        })

        create_remark_comment(self, u'审核通过')
        self.message_post(body=u'审核通过')

    @api.multi
    def manager2_approve(self):
        self.manager1_approve()

    @api.multi
    def hr_expense_sheet_post(self):
        for exp in self:
            state = 'submit'
            if not exp.expense_line_ids:
                raise UserError(u'请填写报销明细')
            department = exp.sudo().department_id
            to_approve_department_id = department.get_to_approve_department(exp.employee_id)
            exp.to_approve_department_id = to_approve_department_id
            if not to_approve_department_id:
                state = 'approve'
            exp.write({'state': state})
            create_remark_comment(exp, u'送审')

            # JPushExtend.send_notification_push(audience=jpush.audience(
            #     jpush.alias(exp.to_approve_id.id)
            # ), notification=exp.expense_no,
            #     body=_("报销单：%s 等待审核") % (self.expense_no))

    @api.multi
    def manager3_approve(self):

        self.manager1_approve()

    @api.multi
    def return_to_approve(self):
        self.state = 'approve'

    @api.multi
    def refuse_expenses(self, reason):
        self.write({'state': 'cancel', 'approve_ids': [(4, self.env.user.id)]})
        for sheet in self:
            body = (_(
                "Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (
                        sheet.name, reason))
            sheet.message_post(body=body)
            sheet.reject_reason = reason

        # JPushExtend.send_notification_push(audience=jpush.audience(
        #     jpush.alias(sheet.create_uid.id)
        # ), notification=_("报销单：%s被拒绝") % (sheet.expense_no),
        #     body=_("原因：%s") % (reason))

    @api.multi
    def create_message_post(self, body_str):
        for sheet in self:
            body = body_str
            sheet.message_post(body=body)

    @api.model
    def create(self, vals):
        if vals.get('expense_no', 'New') == 'New':
            vals['expense_no'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet') or '/'

        return super(HrExpenseSheet, self).create(vals)

    @api.multi
    def write(self, vals):

        if vals.get('state') == 'cancel':
            self.to_approve_department_id = False

        return super(HrExpenseSheet, self).write(vals)

    @api.multi
    def reset_expense_sheets(self):
        self.hr_expense_sheet_post()

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

        amount = self.total_amount - sum(line.amount for line in self.account_payment_line_ids)

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
