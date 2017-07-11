# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError


class AddBomLineWizard(models.TransientModel):
    _name = "add.bom.line.wizard"
    product_id = fields.Many2one('product.product')
    qty = fields.Float()
    product_specs = fields.Char()

    @api.multi
    def action_post(self):
        return {
            'product_id': self.product_id.id,
            'qty': self.qty,
            'product_spec': self.product_specs
        }

        return {'type': 'ir.actions.act_window_close'}
