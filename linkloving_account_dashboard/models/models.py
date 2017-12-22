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
        stock = self.env.ref('linkloving_account.account_account_stock_chart140')
        accumulated_depreciation = self.env['account.account'].search([('name', '=', '固定资产折旧')])
        tax = self.env['account.account'].search([('name', 'like', '应交税费')])
        assets = self.env.ref('l10n_cn_small_business.1_small_business_chart1601')
        # 实收资本
        real_receive_assets = self.env.ref('l10n_cn_small_business.1_small_business_chart3001')
        # 资本公积
        capital_reserves = self.env.ref('l10n_cn_small_business.1_small_business_chart3002')
        # 长期借款
        long_loan = self.env.ref('l10n_cn_small_business.1_small_business_chart2501')

        cashes = self.env['account.account'].search([('user_type_id', '=', cash_type.id)])

        cash_data = sum(cash.get_balance(period_id) for cash in cashes)
        # 流动资产合计
        liquid = cash_data + receivable_amount.get_balance(period_id) + other_receivable_amount.get_balance(
            period_id) + stock.get_balance(period_id)
        # 固定资产原价
        origin_assets = assets.get_balance(period_id) + accumulated_depreciation.balance
        # 固定资产合计
        total_assets = origin_assets + 0
        ## 资产总计=流动+固定
        total_assets_all = total_assets + liquid
        # 流动负债合计
        sub_liabilities = payable_amount.get_balance(period_id) + tax.get_balance(
            period_id) + short_term_borrow.get_balance(period_id)
        # 所有者权益合计
        owner_equity = real_receive_assets.get_balance(period_id) + capital_reserves.get_balance(period_id)

        # 负债合计
        liabilities = sub_liabilities + long_loan.get_balance(period_id)
        # 负债及所有者权益总计
        total_liabilities = liabilities + owner_equity

        res.update({
            'cash_data': {'start': 0, 'current': format_decimal(cash_data, locale='en_US')},
            'short_term_borrow': {'start': 0,
                                  'current': format_decimal(short_term_borrow.get_balance(period_id), locale='en_US')},
            'receivable_amount': {'start': 0,
                                  'current': format_decimal(receivable_amount.get_balance(period_id), locale='en_US')},
            'other_receivable_amount': {'start': 0,
                                        'current': format_decimal(other_receivable_amount.get_balance(period_id),
                                                                  locale='en_US')},
            'stock': {'start': 0, 'current': format_decimal(stock.get_balance(period_id), locale='en_US')},
            'assets': {'start': 0, 'current': format_decimal(assets.get_balance(period_id), locale='en_US')},
            'tax': {'start': 0, 'current': format_decimal(tax.get_balance(period_id), locale='en_US')},
            'short_term_invest': {'start': 0,
                                  'current': format_decimal(short_term_invest.get_balance(period_id), locale='en_US')},
            'real_receive_assets': {'start': 0,
                                    'current': format_decimal(real_receive_assets.get_balance(period_id),
                                                              locale='en_US')},
            'capital_reserves': {'start': 0,
                                 'current': format_decimal(capital_reserves.get_balance(period_id), locale='en_US')},
            'owner_equity': {'start': 0,
                             'current': format_decimal(owner_equity, locale='en_US')},
            'payable_amount': {'start': 0,
                               'current': format_decimal(payable_amount.get_balance(period_id), locale='en_US')},
            'other_payable_amount': {'start': 0,
                                     'current': format_decimal(other_payable_amount.get_balance(period_id),
                                                               locale='en_US')},

            'accumulated_depreciation': {'start': 0,
                                         'current': format_decimal(accumulated_depreciation.get_balance(period_id),
                                                                   locale='en_US')},
            'long_loan': {'start': 0, 'current': format_decimal(long_loan.get_balance(period_id), locale='en_US')},
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
