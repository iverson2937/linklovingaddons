# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import uuid

from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError


class AddBomLineWizard(models.TransientModel):
    _name = "add.bom.line.wizard"
    product_id = fields.Many2one('product.product', string='产品名称')
    name = fields.Char(string='新产品名称')
    to_add = fields.Boolean(string='新建')
    qty = fields.Float()
    product_specs = fields.Text(string=u'规格')

    def _get_return_vals(self):
        process_id = False
        if self.product_id.product_tmpl_id.bom_ids:
            process_id = self.product_id.product_tmpl_id.bom_ids.process_id.name
        return {
            'qty': self.qty,
            'pid': self._context.get('pid'),
            'product_type': self.product_id.product_ll_type,
            'name': self.product_id.name_get(),
            'process_id': process_id,
            'to_add': self.to_add,
            'id': str(uuid.uuid1()),
            'new_name': self.name,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_spec': self.product_specs
        }

    @api.multi
    def action_add(self):
        self._get_return_vals()

    @api.multi
    def action_edit(self):
        self._get_return_vals()
