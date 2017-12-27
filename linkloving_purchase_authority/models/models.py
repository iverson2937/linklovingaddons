# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentRegister(models.Model):
    """
    付款申请表
    """

    _inherit = 'account.payment.register'

    state = fields.Selection(selection_add=[('manager', '经理审核')])

    @api.multi
    def to_manger_approve(self):
        for record in self:
            record.state = 'manager'
