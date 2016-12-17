# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountEmployeeRegisterPaymentWizard(models.TransientModel):
    _name = "account.employee.payable.wizard"
    _description = "Hr Expense Register Payment wizard"

    @api.model
    def _get_default_sheet_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        sheet_id = self.env['hr.expense.sheet'].browse(active_ids)
        return sheet_id

    sheet_id = fields.Many2one('hr.expense.sheet', default=_get_default_sheet_id)

    @api.multi
    def process(self):
        self.sheet_id.deduct_payment()

    @api.multi
    def no_deduct_process(self):
        self.sheet_id.no_deduct_payment()
