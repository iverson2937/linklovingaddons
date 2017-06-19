# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ReturnOfMaterial(models.Model):
    _name = 'mrp.return.material'

    @api.model
    def _default_return_line(self):
        if self._context.get('active_id') and self._context.get('active_model') == "mrp.production":
            product_ids = []
            mrp_production_order = self.env['mrp.production'].browse(self._context['active_id'])
            if mrp_production_order.product_id.bom_ids:
                product_ids = mrp_production_order.product_id.bom_ids[0].bom_line_ids.mapped(
                    'product_id').ids
            if mrp_production_order.is_multi_output:
                product_ids = mrp_production_order.input_product_ids.mapped(
                    'product_id').ids
                print product_ids
            lines = []
            for l in product_ids:
                obj = self.env['return.material.line'].create({
                    'return_qty': 0,
                    'product_id': l,
                })
                lines.append(obj.id)
            return lines
