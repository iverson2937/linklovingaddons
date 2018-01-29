# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockConfigSettings(models.TransientModel):
    _inherit = 'stock.config.settings'

    adjust_stock_account_id = fields.Many2one('account.account', string=u'库存调整科目')

    @api.multi
    def set_adjust_stock_account_id_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'adjust_stock_account_id', self.adjust_stock_account_id.id)
