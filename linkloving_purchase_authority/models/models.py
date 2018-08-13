# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID


class AccountPaymentRegister(models.Model):
    """
    付款申请表
    """

    _inherit = 'account.payment.register'

    state = fields.Selection([
        ('draft', u'Draft'),
        ('posted', u'Post'),
        ('manager', '经理审核'),
        ('confirm', u'Confirm'),
        ('done', u'Done'),
        ('cancel', u'Cancel')
    ], 'State', readonly=True, default='draft', track_visibility='onchange')

    has_to_approve_ids = fields.Boolean(compute='get_to_approve_id')

    can_reject = fields.Boolean(compute='check_can_reject')

    @api.multi
    def check_can_reject(self):
        for p in self:
            if p.state in ('posted', 'confirm', 'manager') and p.create_uid == self.env.user:
                p.can_reject = True
            elif p.state == 'posted' and self.env.user.has_group(
                    'linkloving_purchase_authority.purchase_manager_1'):
                p.can_reject = True
            elif p.state == 'manager' and self.env.user.has_group(
                    'linkloving_purchase_authority.purchase_manager_plus'):
                p.can_reject = True
            elif p.state == 'confirm' and self.env.user.has_group(
                    'linkloving_purchase_authority.purchase_manager_plus'):
                p.can_reject = True
            elif p.state == 'confirm' and self.env.user.has_group('linkloving_purchase_authority.purchase_manager_1'):
                p.can_reject = True
            else:
                p.can_reject = False
    # 审核人
    to_approve_ids = fields.Many2many('res.users', compute='get_to_approve_id')

    @api.multi
    def get_to_approve_id(self):
        for payment in self:
            # 提交状态，一级审核权限的人审核
            if payment.state == 'posted':
                group = self.env.ref('linkloving_purchase_authority.purchase_manager_1')
                payment.to_approve_ids = group.users.filtered(lambda x: x.id != SUPERUSER_ID)
                payment.has_to_approve_ids = True
            # 经理审核，二级审核权限的人审核
            elif payment.state == 'manager':
                group = self.env.ref('linkloving_purchase_authority.purchase_manager_plus')
                payment.to_approve_ids = group.users.filtered(lambda x: x.id != SUPERUSER_ID)
                payment.has_to_approve_ids = True
            else:
                payment.to_approve_ids = False
                payment.has_to_approve_ids = False

    @api.multi
    def to_manager_approve(self):

        for record in self:
            if record.amount <= record.company_id.payment_apply_amount:
                record.get_approve()
                record.state = 'confirm'
            else:
                record.state = 'manager'
            record.manager_id = self.env.user.id

    manager_id = fields.Many2one('res.users')

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """

        if self._context.get('manager'):
            return [('state', 'in', ('manager','posted'))]
        else:
            return super(AccountPaymentRegister, self)._needaction_domain_get()
