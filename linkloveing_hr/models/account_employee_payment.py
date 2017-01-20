# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountEmployeePayment(models.Model):
    _name = 'account.employee.payment'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'create_date desc'
    name = fields.Char()
    employee_id = fields.Many2one('hr.employee',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1))
    department_id = fields.Many2one('hr.department')
    to_approve_id = fields.Many2one('res.users', track_visibility='onchange')
    approve_ids = fields.Many2many('res.users')
    apply_date = fields.Date(default=fields.Date.context_today)
    amount = fields.Float(string=u'申请金额')
    remark = fields.Text(string=u'备注')
    address_home_id = fields.Many2one('res.partner', related='employee_id.address_home_id')
    bank_account_id = fields.Many2one('res.partner.bank', related='employee_id.bank_account_id')
    sheet_ids = fields.One2many('hr.expense.sheet', 'payment_id')
    payment_return = fields.Float(string=u'还款金额')

    @api.one
    @api.depends('sheet_ids')
    def _get_pre_payment_reminding_balance(self):
        used_payment=0
        if self.state == 'paid':
            used_payment =sum([sheet.deduct_amount for sheet in self.sheet_ids])
        self.pre_payment_reminding = self.amount-used_payment-self.payment_return

    pre_payment_reminding = fields.Float(string=u'余额', compute=_get_pre_payment_reminding_balance)

    def _get_is_show(self):
        if self._context.get('uid') == self.to_approve_id.id:
            self.is_show = True
        else:
            self.is_show = False

    is_show = fields.Boolean(compute=_get_is_show)

    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', u'确认'),
                              ('manager1_approve', u'一级审批'),
                              ('manager2_approve', u'二级审批'),
                              ('manager3_approve', u'总经理审批'),
                              ('approve', u'批准'),
                              ('paid', u'已支付'),
                              ('deduct', u'已抵扣'),
                              ('returned', u'已还款')
                              ],
                             readonly=True, default='draft', copy=False, string="Status", store=True,
                             track_visibility='onchange')

    @api.multi
    def submit(self):
        self.state = 'confirm'

        if self.employee_id == self.employee_id.department_id.manager_id:
            department = self.to_approve_id.employee_ids.department_id
            if department.allow_amount and self.amount > department.allow_amount:
                self.write({'state': 'approve'})
            else:
                self.to_approve_id = self.employee_id.department_id.parent_id.manager_id.user_id.id
        else:
            self.to_approve_id = self.employee_id.department_id.manager_id.user_id.id

    @api.multi
    def manager1_approve(self):
        # if self.employee_id == self.employee_id.department_id.manager_id:
        #     self.to_approve_id = self.employee_id.department_id.parent_id.manager_id.user_id.id
        # else:
        department = self.to_approve_id.employee_ids.department_id
        if department.allow_amount and self.amount < department.allow_amount:
            self.to_approve_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

        else:
            self.to_approve_id = department.parent_id.manager_id.user_id.id

            self.write({'state': 'manager1_approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.multi
    def reject(self):
        self.state = 'draft'
        self.to_approve_id = False

    @api.multi
    def manager2_approve(self):
        department = self.to_approve_id.employee_ids.department_id
        if self.amount < department.allow_amount:
            self.to_approve_id = False
            self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

        else:
            self.to_approve_id = department.parent_id.manager_id.user_id.id

            self.write({'state': 'manager2_approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.multi
    def manager3_approve(self):

        self.write({'state': 'approve', 'approve_ids': [(4, self.env.user.id)]})

    @api.multi
    def post(self):

        context = {'default_payment_type': 'outbound', 'default_amount': self.amount}

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
            'name': _('还款'),
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
            print vals['name']
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
        if self.state in ['paid', 'deduct']:
            raise UserError('不能删除已经支付的暂支记录。')
        return super(AccountEmployeePayment, self).unlink()
