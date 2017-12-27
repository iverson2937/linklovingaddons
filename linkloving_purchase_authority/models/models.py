# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentRegister(models.Model):
    """
    付款申请表
    """

    _inherit = 'account.payment.register'

    state = fields.Selection(selection_add=[('manager', '经理审核')])

    @api.multi
    def to_manager_approve(self):
        for record in self:
            record.state = 'manager'

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """

        if self._context.get('manager'):
            return [('state', '=', 'manager')]
        else:
            return super(AccountPaymentRegister, self)._needaction_domain_get()
