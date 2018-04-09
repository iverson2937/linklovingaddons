# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round

import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()

        if self.location_id.valuation_out_account_id:

            acc_src = self.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts_data['stock_input'].id
            # 退货，add by allen
            if self.is_return_material:
                acc_src = accounts_data['stock_output'].id

        if self.location_dest_id.valuation_in_account_id:
            acc_dest = self.location_dest_id.valuation_in_account_id.id

        else:
            acc_dest = accounts_data['stock_output'].id

        # 盘盈
        if self.location_id.usage == "inventory" and self.location_dest_id.usage == 'internal':
            adjust_stock_account_id = self.env['ir.values'].sudo().get_default(
                'stock.config.settings', 'adjust_stock_account_id')
            if not adjust_stock_account_id:
                raise UserError('请联系管理员设置库存调整会计科目')
            acc_src = adjust_stock_account_id

            acc_dest = accounts_data['stock_valuation'].id
        # 盘亏
        if self.location_id.usage == "internal" and self.location_dest_id.usage == 'inventory':

            adjust_stock_account_id = self.env['ir.values'].sudo().get_default(
                'stock.config.settings', 'adjust_stock_account_id')
            if not adjust_stock_account_id:
                raise UserError('请联系管理员设置库存调整会计科目')
            acc_src = accounts_data['stock_valuation'].id
            acc_dest = adjust_stock_account_id
        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(_(
                'You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts'))
        if not acc_src:
            raise UserError(_(
                'Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (
                                self.product_id.name))
        if not acc_dest:
            raise UserError(_(
                'Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (
                                self.product_id.name))
        if not acc_valuation:
            raise UserError(_(
                'You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation
