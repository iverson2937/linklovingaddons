# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrPurchaseRefuseWizard(models.TransientModel):
    _name = "hr.purchase.refuse.wizard"
    _description = "Hr Purchase Refuse Wizard"

    description = fields.Char(string='Reason', required=True)

    @api.multi
    def prepayment_refuse_reason(self):
        self.ensure_one()

        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        purchase_apply = self.env['hr.purchase.apply'].browse(active_ids)
        purchase_apply.refuse_payment(self.description)
        return {'type': 'ir.actions.act_window_close'}
