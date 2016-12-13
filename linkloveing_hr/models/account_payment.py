# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    partner_type = fields.Selection(selection_add=[('employee', 'employee')])
    to_approve_id = fields.Many2one('res.users')

    def _get_default_partner(self):
        return self.env.user.partner_id.id

    partner_id = fields.Many2one('res.partner', default=_get_default_partner)


    approve_ids = fields.Many2many('res.users')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', u'确认'),
                              ('manager1_approve', u'一级审批'),
                              ('manager2_approve', u'二级审批'),
                              ('manager3_approve', u'总经理审批'),
                              ('approve', u'批准'),
                              ('posted', 'Posted'),
                              ('sent', 'Sent'),
                              ('reconciled', 'Reconciled')],
                             readonly=True, default='draft', copy=False, string="Status")

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if not self.invoice_ids:
            # Set default partner type for the payment type
            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        res['domain']['journal_id'] = self.payment_type == 'inbound' and [('at_least_one_inbound', '=', True)] or [
            ('at_least_one_outbound', '=', True)]
        res['domain']['journal_id'].append(('type', 'in', ('bank', 'cash')))
        return res

    @api.multi
    def submit(self):
        self.state = 'confirm'
        employee_id = self.partner_id.user_ids.employee_ids
        if employee_id == employee_id.department_id.manager_id:
            department = self.to_approve_id.employee_ids.department_id
            if department.allow_amount and self.total_amount > department.allow_amount:
                self.write({'state': 'approve'})
            else:
                self.to_approve_id = self.employee_id.department_id.parent_id.manager_id.user_id.id
        else:
            self.to_approve_id = employee_id.department_id.manager_id.user_id.id


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


