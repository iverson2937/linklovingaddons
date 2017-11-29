# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountDashboard(models.Model):
    _inherit = 'account.account'

    @api.model
    def get_dashboard_datas(self):
        cash_data = self.env['account.account'].search([('name', '=', '银行存款')]).balance
        receivable_amount = self.env['account.account'].search([('name', '=', '应收账款')]).balance
        payable_amount = self.env['account.account'].search([('name', '=', '应付账款')]).balance
        other_receivable_amount = self.env['account.account'].search([('name', '=', '其他应收款')]).balance
        stock = self.env['account.account'].search([('name', '=', '库存商品')]).balance
        accumulated_depreciation = self.env['account.account'].search([('name', 'like', '累计折旧')]).balance

        assets = self.env['account.account'].search([('name', '=', '固定资产')]).balance
        short_term_borrow = self.env['account.account'].search([('name', '=', '短期借款')]).balance
        real_receive_assets = self.env['account.account'].search([('name', '=', '实收资本')]).balance
        capital_reserves = self.env['account.account'].search([('name', '=', '资本公积')]).balance

        return {
            'cash_data': cash_data,
            'receivable_amount': receivable_amount,
            'other_receivable_amount': other_receivable_amount,
            'stock': stock,
            'assets': assets,
            'short_term_borrow': short_term_borrow,
            'real_receive_assets': real_receive_assets,
            'capital_reserves': capital_reserves,
            'payable_amount': payable_amount,
            'accumulated_depreciation': accumulated_depreciation,
        }
