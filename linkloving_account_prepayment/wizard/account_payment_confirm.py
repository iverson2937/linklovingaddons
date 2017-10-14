# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentConfirm(models.TransientModel):
    _inherit = 'account.payment.confirm'
    is_prepayment = fields.Boolean(string=u'是否为预付款')
    amount = fields.Float(string=u'金额')

    def post(self):
        pass
