# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountEmployeePaymentLine(models.Model):
    _name = 'account.employee.payment.line'
    sheet_id = fields.Many2one('hr.expense.sheet')
    amount = fields.Float()
    payment_id = fields.Many2one('account.employee.payment')

