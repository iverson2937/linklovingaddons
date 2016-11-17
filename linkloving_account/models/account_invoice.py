# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    invoice = fields.Char(string='Invoice No')
    balance_ids = fields.One2many('account.receive.register.balance', 'invoice_id')
    payment_id = fields.Many2one('account.payment.register')
    remain_apply_balance = fields.Monetary(string='Total in Invoice Currency', currency_field='currency_id',
                                           store=True, readonly=True, compute='_compute_amount',
                                           help="Total amount in the currency of the invoice, negative for credit notes.")

    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice',
                 'balance_ids')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        self.remain_apply_balance = self.amount_total
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
        if len(self.balance_ids) >= 1:
            amount = 0.0
            for balance_id in self.balance_ids:
                amount += balance_id.amount
            print 'eeeeeeeeeeee',amount
            self.remain_apply_balance =  self.remain_apply_balance-amount

    @api.multi
    def write(self, vals):

        return super(AccountInvoice, self).write(vals)
