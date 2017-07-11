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
        process_id = False
        if self.product_id.product_tmpl_id.bom_ids:
            process_id = self.product_id.product_tmpl_id.bom_ids.process_id.name

        return {
            'qty': self.qty,
            'name': self.product_id.name_get(),
            'process_id': process_id,
            'product_spec': self.product_specs
        }
