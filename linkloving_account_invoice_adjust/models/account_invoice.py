# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    is_adjust = fields.Boolean(string='是否为额外添加的')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    adjust_id = fields.Many2one('account.invoice.adjust', string='金额调整')
    adjust_price = fields.Float(string='金额')

    @api.multi
    def _adjust_line_unset(self):
        self.env['account.invoice.line'].search([('invoice_id', 'in', self.ids), ('is_adjust', '=', True)]).unlink()

    @api.multi
    def adjust_set(self):

        # Remove delivery products from the sale order
        self._adjust_line_unset()

        for order in self:
            adjust_id = order.adjust_id
            if adjust_id:
                if order.state not in ('draft', 'post', 'validate'):
                    raise UserError('只有草稿和提交状态的对账单可以修改')

                if adjust_id.type_mode == 'add':
                    sign = 1
                    account_id = adjust_id.property_account_expense_id.id
                else:
                    sign = -1
                    account_id = adjust_id.property_account_income_id.id

                final_price = order.adjust_price * sign
                order._create_adjust_invoice_line(adjust_id, final_price, account_id)

            else:
                raise UserError('没有对账金额调整')

        return True

    def _create_adjust_invoice_line(self, adjust_id, price_unit, account_id):
        AccountInvoiceline = self.env['account.invoice.line']

        # Apply fiscal position
        taxes = adjust_id.product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids

        # Create the sale order line
        values = {
            'invoice_id': self.id,
            'name': adjust_id.name,
            'quantity': 1,
            'uom_id': adjust_id.product_id.uom_id.id,
            'account_id': account_id,
            'product_id': adjust_id.product_id.id,
            'price_unit': price_unit,
            'invoice_line_tax_ids': [(6, 0, taxes_ids)],
            'is_adjust': True,
        }

        sol = AccountInvoiceline.sudo().create(values)
        return sol
