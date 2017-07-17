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
    process_id = fields.Many2one('mrp.process')

    @api.onchange('product_id')
    def _on_product_id(self):
        self.product_specs = self.product_id.product_specs
        self.name = self.product_id.name

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
            'new_name': self.name if self.to_add else self.product_id.name,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_specs': self.product_specs if self.to_add else self.product_id.product_specs
        }

    @api.multi
    def action_add(self):
        return self._get_return_vals()

    @api.multi
    def action_edit(self):
        res = self._get_return_vals()
        res['id'] = self._context.get('pid')
        print res
        return res
