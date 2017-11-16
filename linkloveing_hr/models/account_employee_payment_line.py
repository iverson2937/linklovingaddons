# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountEmployeePaymentLine(models.Model):
    _name = 'account.employee.payment.line'
    sheet_id = fields.Many2one('hr.expense.sheet')
    expense_no = fields.Char(related='sheet_id.expense_no')
    accounting_date = fields.Date(related='sheet_id.accounting_date')
    name = fields.Char(related='sheet_id.name')

    amount = fields.Float()
    payment_id = fields.Many2one('account.employee.payment')
    payment_name = fields.Char(related='payment_id.name')
