# -*- coding: utf-8 -*-

from odoo import models, fields, api
import locale

from babel.numbers import format_decimal

from odoo.exceptions import UserError


class AccountDashboard(models.Model):
    _inherit = 'account.account'

    def get_fiscal_year_begin(self):
        fiscalyear = self.env['account.fiscalyear'].get_current_fiscalyear()
        period_id = fiscalyear.period_ids[0]
        final_data = self.env['account.account.final'].search(
            [('account_id', '=', self.id), ('period_id', '=', period_id.id), ('partner_id', '=', False)])
        return final_data.end_debit - final_data.end_credit

    def get_period_balance(self, period):
        if period.state == 'done':
            final = self.env['account.account.final'].search(
                [('account_id', '=', self.id), ('period_id', '=', period.id), ('partner_id', '=', False)])
            return final.end_debit - final.end_credit
        else:

            return self.balance

    @api.model
    def get_dashboard_datas(self, period=None):
        period_id = self.env['account.period'].browse(period)
        res = {}
        # 短期借款
        short_term_borrow = self.env.ref('l10n_cn_small_business.1_small_business_chart2001')
        # 短期投资
        short_term_invest = self.env.ref('l10n_cn_small_business.1_small_business_chart1101')

        cash_type = self.env.ref('account.data_account_type_liquidity')
        receivable_amount = self.env.ref('l10n_cn_small_business.1_small_business_chart1122')
        payable_amount = self.env.ref('l10n_cn_small_business.1_small_business_chart2202')
        # 其他应付款
        other_payable_amount = self.env.ref('l10n_cn_small_business.1_small_business_chart2241')
        other_receivable_amount = self.env.ref('l10n_cn_small_business.1_small_business_chart1221')
        # 库存商品
        stock_1 = self.env.ref('l10n_cn_small_business.1_small_business_chart1405')
        stock_2 = self.env.ref('linkloving_account.account_account_stock_chart1409')
        stock_3 = self.env.ref('l10n_cn_small_business.1_small_business_chart4001')
        accumulated_depreciation = self.env['account.account'].search([('name', '=', '固定资产折旧')])
        tax = self.env.ref('linkloving_account_tax_inherit.account_account_tax_chart2221')

        total_tax = total_tax_start = total_payable_amount = total_payable_amount_start = 0
        for t in tax.child_ids:
            total_tax += t.get_period_balance(period_id)
            total_tax_start += t.get_fiscal_year_begin()

        payable_amount = self.env.ref('linkloving_account_purchase.account_account_receive')
        for p in payable_amount.child_ids:
            total_payable_amount += p.get_period_balance(period_id)
            total_payable_amount_start += p.get_fiscal_year_begin()

        assets = self.env.ref('l10n_cn_small_business.1_small_business_chart1601')
        # 实收资本
        real_receive_assets = self.env.ref('l10n_cn_small_business.1_small_business_chart3001')
        # 资本公积
        capital_reserves = self.env.ref('l10n_cn_small_business.1_small_business_chart3002')
        # 长期借款
        long_loan = self.env.ref('l10n_cn_small_business.1_small_business_chart2501')

        cashes = self.env['account.account'].search([('user_type_id', '=', cash_type.id)])

        cash_data = start_cash_data = 0

        for cash in cashes:
            cash_data += float(cash.get_period_balance(period_id))
            start_cash_data += float(cash.get_fiscal_year_begin())
        stock = stock_1.get_period_balance(period_id) + stock_2.get_period_balance(
            period_id) + stock_3.get_period_balance(period_id)
        start_stock = stock_1.get_fiscal_year_begin() + stock_2.get_fiscal_year_begin() + stock_3.get_fiscal_year_begin()

        # 流动资产合计
        liquid = cash_data + receivable_amount.get_period_balance(
            period_id) + other_receivable_amount.get_period_balance(
            period_id) + stock
        liquid_start = start_cash_data + receivable_amount.get_fiscal_year_begin() + other_receivable_amount.get_fiscal_year_begin() + start_stock
        # 固定资产原价
        origin_assets = assets.get_period_balance(period_id) + accumulated_depreciation.get_period_balance(period_id)
        origin_assets_start = assets.get_fiscal_year_begin() + accumulated_depreciation.get_fiscal_year_begin()
        # 固定资产合计
        total_assets = origin_assets + 0
        total_assets_start = origin_assets_start + 0
        ## 资产总计=流动+固定
        total_assets_all = total_assets + liquid
        total_assets_all_start = total_assets_start + liquid_start
        # 流动负债合计
        sub_liabilities = total_payable_amount + total_tax + short_term_borrow.get_period_balance(period_id)
        sub_liabilities_start = total_payable_amount_start + total_tax_start + short_term_borrow.get_fiscal_year_begin()
        # 所有者权益合计
        owner_equity = real_receive_assets.get_period_balance(period_id) + capital_reserves.get_period_balance(
            period_id)
        owner_equity_start = real_receive_assets.get_fiscal_year_begin() + capital_reserves.get_fiscal_year_begin()

        # 负债合计
        liabilities = sub_liabilities + long_loan.get_period_balance(period_id)
        liabilities_start = sub_liabilities_start + long_loan.get_fiscal_year_begin()
        # 负债及所有者权益总计
        total_liabilities = liabilities + owner_equity
        total_liabilities_start = liabilities_start + owner_equity_start

        res.update({
            'cash_data': {'start': format_decimal(start_cash_data, locale='en_US'),
                          'current': format_decimal(cash_data, locale='en_US')},
            'short_term_borrow': {'start': format_decimal(short_term_borrow.get_fiscal_year_begin(), locale='en_US'),
                                  'current': format_decimal(short_term_borrow.get_period_balance(period_id),
                                                            locale='en_US')},
            'receivable_amount': {'start': format_decimal(receivable_amount.get_fiscal_year_begin(), locale='en_US'),
                                  'current': format_decimal(receivable_amount.get_period_balance(period_id),
                                                            locale='en_US')},
            'other_receivable_amount': {'start': format_decimal(other_receivable_amount.get_fiscal_year_begin(),
                                                                locale='en_US'),
                                        'current': format_decimal(other_receivable_amount.get_period_balance(period_id),
                                                                  locale='en_US')},
            'stock': {'start': format_decimal(start_stock, locale='en_US'),
                      'current': format_decimal(stock, locale='en_US')},
            'assets': {'start': format_decimal(assets.get_fiscal_year_begin(), locale='en_US'),
                       'current': format_decimal(assets.get_period_balance(period_id), locale='en_US')},
            'tax': {'start': format_decimal(total_tax_start, locale='en_US'),
                    'current': format_decimal(total_tax, locale='en_US')},
            'short_term_invest': {'start': format_decimal(short_term_invest.get_fiscal_year_begin(),
                                                          locale='en_US'),
                                  'current': format_decimal(short_term_invest.get_period_balance(period_id),
                                                            locale='en_US')},
            'real_receive_assets': {'start': format_decimal(real_receive_assets.get_fiscal_year_begin(),
                                                            locale='en_US'),
                                    'current': format_decimal(real_receive_assets.get_period_balance(period_id),
                                                              locale='en_US')},
            'capital_reserves': {'start': format_decimal(capital_reserves.get_fiscal_year_begin(),
                                                         locale='en_US'),
                                 'current': format_decimal(capital_reserves.get_period_balance(period_id),
                                                           locale='en_US')},
            'owner_equity': {'start': format_decimal(owner_equity_start, locale='en_US'),
                             'current': format_decimal(owner_equity, locale='en_US')},
            'payable_amount': {'start':format_decimal(total_payable_amount_start, locale='en_US'),
                               'current': format_decimal(total_payable_amount, locale='en_US')},
            'other_payable_amount': {'start': format_decimal(other_payable_amount.get_fiscal_year_begin(),
                                                               locale='en_US'),
                                     'current': format_decimal(other_payable_amount.get_period_balance(period_id),
                                                               locale='en_US')},

            'accumulated_depreciation': {'start': format_decimal(
                                             accumulated_depreciation.get_fiscal_year_begin(),locale='en_US'),
                                         'current': format_decimal(
                                             accumulated_depreciation.get_period_balance(period_id),
                                             locale='en_US')},
            'long_loan': {'start': format_decimal(long_loan.get_fiscal_year_begin(), locale='en_US'),
                          'current': format_decimal(long_loan.get_period_balance(period_id), locale='en_US')},
            'liquid': {'start': format_decimal(liquid_start, locale='en_US'),
                       'current': format_decimal(liquid, locale='en_US')},
            'origin_assets': {'start': format_decimal(origin_assets_start, locale='en_US'), 'current': format_decimal(origin_assets, locale='en_US')},

            'total_assets': {'start': format_decimal(total_assets_start, locale='en_US'), 'current': format_decimal(total_assets, locale='en_US')},

            'total_assets_all': {'start': format_decimal(total_assets_all_start, locale='en_US'),
                                 'current': format_decimal(total_assets_all, locale='en_US')},
            'sub_liabilities': {'start': format_decimal(sub_liabilities_start, locale='en_US'), 'current': format_decimal(sub_liabilities, locale='en_US')},
            'liabilities': {'start': format_decimal(liabilities_start, locale='en_US'), 'current': format_decimal(liabilities, locale='en_US')},
            'total_liabilities': {'start': format_decimal(total_liabilities, locale='en_US'), 'current': format_decimal(total_liabilities, locale='en_US')}
        })

        return res

    def get_account_data(self, account_id, period):

        period_data = self.env['account.account.final'].search(
            [('period_id', '=', period), ('account_id', '=', account_id)])
        return period_data.debit - period_data.credit

    @api.model
    def get_period(self):
        current_period_id = self.env['account.period'].search([('state', '!=', 'done')])[0]
        periods = self.env['account.period'].search([])
        res = []
        for period in periods:
            res.append({
                'id': period.id,
                'name': period.name
            })
        return {
            'current_period': {
                'id': current_period_id.id,
                'name': current_period_id.name
            },
            'periods': res
        }
