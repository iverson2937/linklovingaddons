# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        if self.invoice_ids:
            self.destination_account_id = self.invoice_ids[0].account_id.id
        elif self.payment_type == 'transfer':
            if not self.company_id.transfer_account_id.id:
                raise UserError(_('Transfer account not defined on the company.'))
            self.destination_account_id = self.company_id.transfer_account_id.id
        elif self.partner_id:
            if self.partner_type == 'customer':
                self.destination_account_id = self.partner_id.prepayment_account_id.id
            elif self.partner_type == 'other':
                self.destination_account_id = self.receive_account_id
            else:
                self.destination_account_id = self.partner_id.property_account_payable_id.id
        # 收款销售确认
        elif not self.partner_id:
            if self._context.get('to_sales') and self.partner_type == 'customer':
                self.destination_account_id = self.partner_id.prepayment_account_id.id
