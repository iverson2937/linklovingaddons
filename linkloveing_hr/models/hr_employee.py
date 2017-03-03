# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    payment_ids = fields.One2many('account.employee.payment', 'employee_id')

    @api.one
    @api.depends('payment_ids')
    def _get_pre_payment_reminding(self):
        self.pre_payment_reminding=sum([payment_id.pre_payment_reminding if payment_id.state =='paid' else 0 for payment_id in self.payment_ids])
    pre_payment_reminding = fields.Float(compute=_get_pre_payment_reminding)
