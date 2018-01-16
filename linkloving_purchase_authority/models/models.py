# -*- coding: utf-8 -*-

from odoo import models, fields, api


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
            return [('state', '=', 'manager')]
        else:
            return super(AccountPaymentRegister, self)._needaction_domain_get()
