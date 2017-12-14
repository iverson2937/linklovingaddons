# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _anglo_saxon_sale_move_lines(self, i_line):
        """Return the additional move lines for sales invoices and refunds.

        i_line: An account.invoice.line object.
        res: The move line entries produced so far by the parent move_line_get.
        """
        inv = i_line.invoice_id
        company_currency = inv.company_id.currency_id

        if i_line.product_id.type == 'product' and i_line.product_id.valuation == 'real_time':
            fpos = i_line.invoice_id.fiscal_position_id
            accounts = i_line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)
            # debit account dacc will be the output account
            dacc = accounts['stock_output'].id
            # credit account cacc will be the expense account
            cacc = accounts['expense'].id
            print dacc
            print cacc
            if dacc and cacc:
                price_unit = i_line._get_anglo_saxon_price_unit()
                if inv.currency_id != company_currency:
                    currency_id = inv.currency_id.id
                    amount_currency = i_line._get_price(company_currency, price_unit)
                else:
                    currency_id = False
                    amount_currency = False
                return [
                    {
                        'type': 'src',
                        'name': i_line.name[:64],
                        'price_unit': price_unit,
                        'quantity': i_line.quantity,
                        'price': price_unit * i_line.quantity,
                        'currency_id': currency_id,
                        'amount_currency': amount_currency,
                        'account_id': dacc,
                        'product_id': i_line.product_id.id,
                        'uom_id': i_line.uom_id.id,
                        'account_analytic_id': i_line.account_analytic_id.id,
                        'analytic_tag_ids': i_line.analytic_tag_ids.ids and [
                            (6, 0, i_line.analytic_tag_ids.ids)] or False,
                    },

                    {
                        'type': 'src',
                        'name': i_line.name[:64],
                        'price_unit': price_unit,
                        'quantity': i_line.quantity,
                        'price': -1 * price_unit * i_line.quantity,
                        'currency_id': currency_id,
                        'amount_currency': -1 * amount_currency,
                        'account_id': cacc,
                        'product_id': i_line.product_id.id,
                        'uom_id': i_line.uom_id.id,
                        'account_analytic_id': i_line.account_analytic_id.id,
                        'analytic_tag_ids': i_line.analytic_tag_ids.ids and [
                            (6, 0, i_line.analytic_tag_ids.ids)] or False,
                    },
                ]
        return []
