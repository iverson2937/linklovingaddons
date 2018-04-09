# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ReturnOfMaterial1(models.Model):
    _inherit = 'mrp.return.material'

    @api.model
    def _default_return_line(self):
        if self._context.get('active_id') and self._context.get('active_model') == "mrp.production":
            product_ids = []
            mrp_production_order = self.env['mrp.production'].browse(self._context['active_id'])
            if mrp_production_order.product_id.bom_ids:
                product_ids = mrp_production_order.product_id.bom_ids[0].bom_line_ids.mapped(
                    'product_id').ids
            if mrp_production_order.is_multi_output:
                product_ids = mrp_production_order.rule_id.input_product_ids.mapped(
                    'product_id').ids
            if mrp_production_order.is_random_output:
                product_ids = mrp_production_order.input_product_ids.mapped(
                    'product_id').ids
            lines = []
            for l in product_ids:
                obj = self.env['return.material.line'].create({
                    'return_qty': 0,
                    'product_id': l,
                })
                lines.append(obj.id)
            return lines

    return_ids = fields.One2many('return.material.line', 'return_id', default=_default_return_line)

    # @api.multi
    # def do_return(self):
    #     if self._context.get('is_checking'):
    #         self.state = 'done'
    #     if self.state == 'done':
    #         for r in self.return_ids:
    #             if r.return_qty == 0:
    #                 continue
    #             move = self.env['stock.move'].create(self._prepare_move_values(r))
    #             r.return_qty = 0
    #             move.action_done()
    #         # Fix ME
    #         # self.return_ids.create_scraps()
    #         self.production_id.write({'state': 'done'})
    #     else:
    #         self.production_id.write({'state': 'waiting_warehouse_inspection'})
    #     return True
