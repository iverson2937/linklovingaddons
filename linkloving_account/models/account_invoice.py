# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    invoice = fields.Char(string='Invoice No')
    balance_ids = fields.One2many('account.payment.register.balance', 'invoice_id')
    payment_ids = fields.Many2many('account.payment.register', 'account_invoice_account_payment_register_rel',
                                   'account_invoice_id', 'account_payment_register_id')
    remain_apply_balance = fields.Monetary(string='To Apply', currency_field='currency_id',
                                           store=True, readonly=True, compute='_compute_amount',
                                           help="Total amount in the currency of the invoice, negative for credit notes.")

    @api.one
    def auto_set_to_done(self):
        if self.state == 'open':
            domain = [('account_id', '=', self.account_id.id),
                      ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                      ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
            if self.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
            lines = self.env['account.move.line'].search(domain)
            for line in lines:
                if self.has_outstanding:
                    self.assign_outstanding_credit(line.id)

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice',
                 'balance_ids')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_untaxed_o = sum(line.price_subtotal_o for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        self.amount_total_o = sum(line.price_subtotal_o for line in self.invoice_line_ids)

        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign
        self.remain_apply_balance = self.amount_total * sign
        if len(self.balance_ids) >= 1:
            amount = 0.0
            for balance_id in self.balance_ids:
                amount += balance_id.amount
            self.remain_apply_balance = self.remain_apply_balance - amount


class AcLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit
        taxes = False
        # print self.invoice_line_tax_ids
        # if self.invoice_line_tax_ids:
        #     print '-----------------------------------'
        #     taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        #     print taxes
        #     print taxes['total_excluded']
        self.price_subtotal = price_subtotal_signed = -self.quantity * price
        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id.date_invoice).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign