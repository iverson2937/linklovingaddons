# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from .hr_expense_sheet import create_remark_comment
from odoo.addons import decimal_precision as dp


class AccountEmployeePayment(models.Model):
    '''
    暂支model
    '''
    _name = 'account.employee.payment'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'create_date desc'
    name = fields.Char()

    remark_comments_ids = fields.One2many('hr.remark.comment', 'employee_payment_id', string=u'审核记录')

    def _get_account_date(self):
        for p in self:
            p.accounting_date = p.apply_date

    accounting_date = fields.Date(string=u'会计日期')
    employee_id = fields.Many2one('hr.employee',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1))
    payment_ids = fields.One2many('account.payment', 'res_id', domain=[('res_model', '=', 'account.employee.payment'),
                                                                       ('payment_type', '=', 'outbound')])
    return_ids = fields.One2many('account.payment', 'res_id', domain=[('res_model', '=', 'account.employee.payment'),
                                                                      ('payment_type', '=', 'inbound')])
    payment_reminding = fields.Float(related='employee_id.pre_payment_reminding')

    to_approve_department_id = fields.Many2one('hr.department', readonly=True, string=u'待审核部门',
                                               compute='_get_to_approve_department', store=True)

    @api.multi
    def _get_to_approve_department(self):
        for sheet in self:
            if sheet.to_approve_id:
                sheet.to_approve_department_id = sheet.to_approve_id.employee_ids[0].department_id.id

    def _get_paid_amount(self):
        for record in self:
            record.paid_amount = sum(payment.amount for payment in record.payment_ids)

    paid_amount = fields.Float(compute=_get_paid_amount)

    @api.multi
    def _compute_has_payment_ids(self):
        for sheet in self:

            if sheet.payment_ids:
                sheet.has_payment_ids = True
            else:
                sheet.has_payment_ids = False

    has_payment_ids = fields.Boolean(compute=_compute_has_payment_ids)

    @api.multi
    def refuse_payment(self, reason):
        self.write({'state': 'cancel', 'approve_ids': [(4, self.env.user.id)]})
        for sheet in self:
            body = (_(
                "Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (
                        sheet.name, reason))
            sheet.message_post(body=body)
            sheet.to_approve_id = False
            # 拒絕取消暂支抵扣
            if sheet.payment_line_ids:
                for line in sheet.payment_line_ids:
                    line.unlink()

            create_remark_comment(sheet, u'拒绝')

    def _get_account_date(self):
        for p in self:
            p.department_id = p.employee_id.department_id.id

    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    department_id = fields.Many2one('hr.department', compute='_get_department_id', store=True)
    to_approve_id = fields.Many2one('res.users', compute='_get_to_approve_id', store=True)

    @api.multi
    @api.depends('to_approve_department_id')
    def _get_to_approve_id(self):

        for sheet in self:
            if sheet.to_approve_department_id:
                sheet.to_approve_id = sheet.to_approve_department_id.manager_id.sudo().user_id

    approve_ids = fields.Many2many('res.users')
    apply_date = fields.Date(default=fields.Date.context_today)
    amount = fields.Float(string='Apply Amount')
    remark = fields.Text(string='Remark')
    address_home_id = fields.Many2one('res.partner', related='employee_id.address_home_id')
    bank_account_id = fields.Many2one('res.partner.bank', related='employee_id.bank_account_id')

    # FIXME:USE BETTER WAY TO HIDE THE BUTTON
    def _get_is_show(self):
        is_show = False
        if self.env.user.id == self.to_approve_id.id:
            is_show = True
        self.is_show = is_show

    is_show = fields.Boolean(compute=_get_is_show)

    @api.one
    @api.depends('return_ids')
    def _get_return_balance(self):
        self.payment_return = sum([return_id.amount for return_id in self.return_ids])

    payment_return = fields.Float(string='Return amount', compute=_get_return_balance)
    return_count = fields.Integer(compute='_get_count')
    payment_count = fields.Integer(compute='_get_count')
    # 暂支抵扣明细
    payment_line_ids = fields.One2many('account.employee.payment.line', 'payment_id')

    @api.one
    @api.depends('payment_count', 'payment_return')
    def _get_pre_payment_reminding_balance(self):
        self.pre_payment_reminding = 0.0
        used_payment = 0
        if self.state == 'paid':
            used_payment = sum([payment.amount for payment in self.payment_line_ids])
            self.pre_payment_reminding = self.amount - used_payment - self.payment_return

    pre_payment_reminding = fields.Float(string='Available amount', compute=_get_pre_payment_reminding_balance,
                                         digits=dp.get_precision('Payroll'))

    @api.one
    @api.depends('state', 'return_ids', 'payment_line_ids')
    def _is_can_return(self):
        if self.state == 'paid':
            self.can_return = True
        payment_return = sum([return_id.amount for return_id in self.return_ids])
        used_payment = sum([payment.amount for payment in self.payment_line_ids])
        remaining = self.amount - used_payment - payment_return

        if float_is_zero(remaining, 2):
            self.can_return = False

    can_return = fields.Boolean(compute=_is_can_return, store=True)

    def _get_is_show(self):
        if self._context.get('uid') == self.to_approve_id.id:
            self.is_show = True
        else:
            self.is_show = False

    is_show = fields.Boolean(compute=_get_is_show)

    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', u'Confirm'),
                              ('manager1_approve', u'1st Approved'),
                              ('manager2_approve', u'2nd Approved'),
                              ('manager3_approve', u'General Manager Approve'),
                              ('approve', u'Approved'),
                              ('cancel', u'取消'),
                              ('paid', u'Paid'),
                              ],
                             readonly=True, default='draft', copy=False, string="Status", store=True,
                             track_visibility='onchange')

    @api.depends('payment_line_ids', 'return_ids')
    def _get_count(self):
        """

        """
        for payment in self:
            payment.update({
                'payment_count': len(set(payment.payment_line_ids.ids)),
                'return_count': len(set(payment.return_ids.ids))
            })

    to_approve_department_id = fields.Many2one('hr.department', readonly=True, string=u'待审核部门',
                                               compute='_get_to_approve_department')

    @api.multi
    def _get_to_approve_department(self):
        for sheet in self:
            if sheet.to_approve_id:
                sheet.to_approve_department_id = sheet.to_approve_id.employee_ids[0].department_id.id

    @api.multi
    def submit(self):
        self.state = 'confirm'
        if not self.employee_id.department_id:
            raise UserError('请设置员工所在部门')
        department = self.employee_id.department_id
        if not department.manager_id:
            raise UserError(u'请设置部门审核人')
        if self.employee_id == department.manager_id:
            if not department.parent_id.manager_id:
                raise UserError(u'上级部门未设置审核人')
            self.to_approve_department_id = department.parent_id.id
        else:
            self.to_approve_department_id = department.id

        create_remark_comment(self, u"送审")

    @api.multi
    def manager1_approve(self):
        department = self.to_approve_department_id
        if not department.parent_id or (department.allow_amount and self.total_amount < department.allow_amount):
            self.to_approve_department_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

        else:
            if not department.parent_id.manager_id:
                raise UserError(u'上级部门没有设置经理,请联系管理员')

            self.to_approve_department_id = department.parent_id.id

            self.write({'approve_ids': [(4, self.env.user.id)]})

        create_remark_comment(self, u'审核通过')

    @api.multi
    def create_message_post(self, body_str):
        for sheet in self:
            body = body_str
            sheet.message_post(body=body)

    @api.multi
    def cancel(self):

        self.state = 'cancel'

    @api.multi
    def manager2_approve(self):
        self.manager1_approve()

    @api.multi
    def manager3_approve(self):

        self.manager1_approve()

    @api.multi
    def post(self):

        context = {'default_payment_type': 'outbound', 'default_amount': self.amount - self.paid_amount}

        return {
            'name': _('payment'),
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': False,
            'res_model': 'account.employee.register.payment.wizard',
            'domain': [],
            'context': dict(context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def return_payment(self):

        context = {'default_payment_type': 'inbound', 'default_amount': self.pre_payment_reminding}

        return {
            'name': _('Return Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': False,
            'res_model': 'account.employee.register.payment.wizard',
            'domain': [],
            'context': dict(context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.employee.payment') or '/'
        return super(AccountEmployeePayment, self).create(vals)

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        if self._context.get('to_approve_id'):
            return [('to_approve_id', '=', self.env.user.id)]
        if self._context.get('wait_pay'):
            return [('state', '=', 'approve')]
        if self._context.get('search_default_approved'):
            return [('state', '=', 'post')]

    @api.multi
    def unlink(self):
        if self.state not in ['draft', 'cancel']:
            raise UserError('只可以删除草稿状态的暂支.')
        return super(AccountEmployeePayment, self).unlink()
