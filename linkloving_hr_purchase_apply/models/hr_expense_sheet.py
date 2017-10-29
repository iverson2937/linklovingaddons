# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    apply_line_ids = fields.Many2one('hr.purchase.apply.line', 'sheet_id')

    @api.onchange('apply_line_ids')
    def on_change_apply_line_ids(self):
        if self.apply_line_ids:
            for line_id in self.apply_line_ids:
                self.env['hr.expense'].crate({
                    'product_id': line_id.product_id.id,
                    'quantity': line_id.product_qty,
                    'price_unit': line_id.price_unit,
                    'name': line_id.decription,
                })
