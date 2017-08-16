# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountEmployeeRefuseWizard(models.TransientModel):
    _name = "account.employee.refuse.wizard"
    _description = "Account Employee Refuse Wizard"

    description = fields.Char(string='Reason', required=True)

    @api.multi
    def prepayment_refuse_reason(self):
        self.ensure_one()

        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        payment = self.env['account.employee.payment'].browse(active_ids)
        payment.refuse_payment(self.description)
        return {'type': 'ir.actions.act_window_close'}
