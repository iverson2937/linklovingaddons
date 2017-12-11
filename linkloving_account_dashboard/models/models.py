# -*- coding: utf-8 -*-

from odoo import models, fields, api
import locale

from babel.numbers import format_decimal


class AccountDashboard(models.Model):
    _inherit = 'account.account'

    @api.model
    def get_dashboard_datas(self, period=None):
        period_id = self.env['account.period'].browse(period)
        res = {}
        short_term_borrow = self.env.ref('l10n_cn_small_business.1_small_business_chart1101')
        cash_type = self.env.ref('account.data_account_type_liquidity')
        receivable_amount = self.env.ref('l10n_cn_small_business.1_small_business_chart1122')
        payable_amount = self.env.ref('l10n_cn_small_business.1_small_business_chart2202')
        # 其他应付款
        other_payable_amount = self.env.ref('l10n_cn_small_business.1_small_business_chart2241')
        other_receivable_amount = self.env.ref('l10n_cn_small_business.1_small_business_chart1221')
        stock = self.env['account.account'].search([('name', '=', '库存商品')])

        accumulated_depreciation = self.env['account.account'].search([('name', '=', '固定资产折旧')])

        tax = self.env['account.account'].search([('name', 'like', '应交税费')])

        assets = self.env.ref('l10n_cn_small_business.1_small_business_chart1601')

        real_receive_assets = self.env.ref('l10n_cn_small_business.1_small_business_chart3001')
        capital_reserves = self.env.ref('l10n_cn_small_business.1_small_business_chart3002')
        # 长期借款
        long_loan = self.env.ref('l10n_cn_small_business.1_small_business_chart2501')
        cashes = self.env['account.account'].search([('user_type_id', 'like', cash_type.id)])
        if period_id.state != 'done':

            cash_data = sum(cash.balance for cash in cashes)
            # 流动资产合计
            liquid = cash_data + receivable_amount.balance + other_receivable_amount.balance + stock.balance
            # 固定资产原价
            origin_assets = assets.balance + accumulated_depreciation.balance
            # 固定资产合计
            total_assets = origin_assets + 0
            ## 资产总计=流动+固定
            total_assets_all = total_assets + liquid
            # 流动负债合计
            sub_liabilities = payable_amount.balance + tax.balance
            # 负债合计
            liabilities = sub_liabilities + long_loan.balance
            # 负债及所有者权益总计
            total_liabilities = liabilities

            res.update({
                'cash_data': {'start': 0, 'current': format_decimal(cash_data, locale='en_US')},
                'receivable_amount': {'start': 0, 'current': format_decimal(receivable_amount.balance, locale='en_US')},
                'other_receivable_amount': {'start': 0,
                                            'current': format_decimal(other_receivable_amount.balance, locale='en_US')},
                'stock': {'start': 0, 'current': format_decimal(stock.balance, locale='en_US')},
                'assets': {'start': 0, 'current': format_decimal(assets.balance, locale='en_US')},
                'tax': {'start': 0, 'current': format_decimal(tax.balance, locale='en_US')},
                'short_term_borrow': {'start': 0, 'current': format_decimal(short_term_borrow.balance, locale='en_US')},
                'real_receive_assets': {'start': 0,
                                        'current': format_decimal(real_receive_assets.balance, locale='en_US')},
                'capital_reserves': {'start': 0, 'current': format_decimal(capital_reserves.balance, locale='en_US')},
                'payable_amount': {'start': 0, 'current': format_decimal(payable_amount.balance, locale='en_US')},
                'other_payable_amount': {'start': 0,
                                         'current': format_decimal(other_payable_amount.balance, locale='en_US')},
                'accumulated_depreciation': {'start': 0, 'current': format_decimal(accumulated_depreciation.balance,
                                                                                   locale='en_US')},
                'long_loan': {'start': 0, 'current': format_decimal(long_loan.balance, locale='en_US')},
            })
        else:
            cash_data = 0
            for cash in cashes:
                balance = self.get_account_data(cash.id, period)
                cash_data + balance
            liquid = cash_data + self.get_account_data(receivable_amount, period) + self.get_account_data(
                other_receivable_amount, period) + self.get_account_data(stock, period)
            # 固定资产原价
            origin_assets = self.get_account_data(assets, period) + self.get_account_data(accumulated_depreciation,
                                                                                          period)
            # 固定资产合计
            total_assets = origin_assets + 0
            ## 资产总计=流动+固定
            total_assets_all = total_assets + liquid
            # 流动负债合计
            sub_liabilities = self.get_account_data(payable_amount, period) + self.get_account_data(-tax, period)
            # 负债合计
            liabilities = sub_liabilities + long_loan.balance
            # 负债及所有者权益总计
            total_liabilities = liabilities

            res.update({
                'cash_data': {'start': 0, 'current': format_decimal(cash_data, locale='en_US')},
                'receivable_amount': {'start': 0,
                                      'current': format_decimal(self.get_account_data(receivable_amount, period),
                                                                locale='en_US')},
                'other_receivable_amount': {'start': 0,
                                            'current': format_decimal(
                                                self.get_account_data(other_receivable_amount, period),
                                                locale='en_US')},
                'stock': {'start': 0, 'current': format_decimal(self.get_account_data(stock, period), locale='en_US')},
                'assets': {'start': 0,
                           'current': format_decimal(self.get_account_data(assets, period), locale='en_US')},
                'tax': {'start': 0, 'current': format_decimal(self.get_account_data(-tax, period), locale='en_US')},
                'short_term_borrow': {'start': 0,
                                      'current': format_decimal(self.get_account_data(short_term_borrow, period),
                                                                locale='en_US')},
                'real_receive_assets': {'start': 0,
                                        'current': format_decimal(self.get_account_data(real_receive_assets, period),
                                                                  locale='en_US')},
                'capital_reserves': {'start': 0,
                                     'current': format_decimal(self.get_account_data(capital_reserves, period),
                                                               locale='en_US')},
                'payable_amount': {'start': 0, 'current': format_decimal(self.get_account_data(payable_amount, period),
                                                                         locale='en_US')},
                'other_payable_amount': {'start': 0,
                                         'current': format_decimal(self.get_account_data(other_payable_amount, period),
                                                                   locale='en_US')},
                'accumulated_depreciation': {'start': 0, 'current': format_decimal(
                    self.get_account_data(accumulated_depreciation, period),
                    locale='en_US')},
                'long_loan': {'start': 0,
                              'current': format_decimal(self.get_account_data(long_loan, period), locale='en_US')},

            })
        res.update({
            'liquid': {'start': 0,
                       'current': format_decimal(liquid, locale='en_US')},
            'origin_assets': {'start': 0, 'current': format_decimal(origin_assets, locale='en_US')},

            'total_assets': {'start': 0, 'current': format_decimal(total_assets, locale='en_US')},

            'total_assets_all': {'start': 0,
                                 'current': format_decimal(total_assets_all, locale='en_US')},
            'sub_liabilities': {'start': 0, 'current': format_decimal(sub_liabilities, locale='en_US')},
            'liabilities': {'start': 0, 'current': format_decimal(liabilities, locale='en_US')},
            'total_liabilities': {'start': 0, 'current': format_decimal(total_liabilities, locale='en_US')}
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
