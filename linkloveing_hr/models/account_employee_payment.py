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
    amount = fields.Float(string='Apply Amount')
    remark = fields.Text(string='Remark')
    address_home_id = fields.Many2one('res.partner', related='employee_id.address_home_id')
    bank_account_id = fields.Many2one('res.partner.bank', related='employee_id.bank_account_id')
    sheet_ids = fields.One2many('hr.expense.sheet', 'payment_id')
    return_ids = fields.One2many('account.employee.payment.return', 'payment_id')

    @api.one
    @api.depends('return_ids')
    def _get_return_balance(self):
        self.payment_return = sum([return_id.amount for return_id in self.return_ids])

    payment_return = fields.Float(string='Return amount', compute=_get_return_balance)
    return_count = fields.Integer(compute='_get_count')
    sheet_count = fields.Integer(compute='_get_count')
    payment_line_ids = fields.One2many('account.employee.payment.line', 'payment_id')

    @api.one
    @api.depends('sheet_ids', 'payment_return')
    def _get_pre_payment_reminding_balance(self):
        self.pre_payment_reminding = 0.0
        used_payment = 0
        if self.state == 'paid':
            used_payment = sum([payment.amount for payment in self.payment_line_ids])
            self.pre_payment_reminding = self.amount - used_payment - self.payment_return

    pre_payment_reminding = fields.Float(string='Available amount', compute=_get_pre_payment_reminding_balance)

    @api.one
    @api.depends('state', 'return_ids', 'payment_line_ids')
    def _is_can_return(self):
        if self.state == 'paid':
            self.can_return = True
        payment_return = sum([return_id.amount for return_id in self.return_ids])
        used_payment = sum([payment.amount for payment in self.payment_line_ids])
        remaining = self.amount - used_payment - payment_return
        if not remaining:
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
                              ('paid', u'Paid'),
                              ],
                             readonly=True, default='draft', copy=False, string="Status", store=True,
                             track_visibility='onchange')

    @api.depends('sheet_ids', 'return_ids')
    def _get_count(self):
        """

        """
        for payment in self:
            payment.update({
                'sheet_count': len(set(self.sheet_ids.ids)),
                'return_count': len(set(self.return_ids.ids))
            })

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
            raise UserError('Can not delete the Expense Sheet which already paid.')
        return super(AccountEmployeePayment, self).unlink()
