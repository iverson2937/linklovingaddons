# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    move_id = fields.Many2one('account.move')

    @api.multi
    def create_account_move(self):
        for line in self:
            self.env['account.move'].create({
                ''
            })

    @api.multi
    def write(self, vals):
        for line in self:
            if vals.get('invoice_status') and vals.get('invoice_status') == 'done':
                if not line.move_id:
                    line.create_account_move()
                else:
                    line.move_id.unlink()
                    line.create_account_move()
        return super(SaleOrderLine, self).write(vals)
