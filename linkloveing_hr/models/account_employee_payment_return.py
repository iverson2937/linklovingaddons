# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountEmployeePaymentReturn(models.Model):
    """
    暂支还款记录
    """
    _name = 'account.employee.payment.return'
    _order = 'create_date desc'
    employee_id = fields.Many2one('hr.employee')
    payment_id = fields.Many2one('account.employee.payment')
    amount = fields.Float(string=u'Return Amount')
