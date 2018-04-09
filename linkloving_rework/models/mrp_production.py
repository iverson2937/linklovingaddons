# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    is_rework = fields.Boolean(related='process_id.is_rework', store=True)
    rework_material_line_ids = fields.One2many('rework.material.line', 'mo_id')

    @api.onchange('process_id')
    def onchange_process_id(self):
        if self.process_id.is_rework:
            self.is_rework = True
        else:
            self.is_rework = False

    def _generate_raw_moves(self, exploded_lines):
        self.ensure_one()
        moves = self.env['stock.move']
        source_location = self.picking_type_id.default_location_src_id
        if self.is_rework:
            if not self.rework_material_line_ids:
                raise UserError(u'请添加重工物料')
            for line_id in self.rework_material_line_ids:
                print line_id.product_qty, 'line_id.product_qty'
                data = {
                    'name': self.name,
                    'date': self.date_planned_start,
                    'product_id': line_id.product_id.id,
                    'product_uom_qty': line_id.product_qty,
                    'product_uom': line_id.product_id.uom_id.id,
                    'location_id': source_location.id,
                    'location_dest_id': line_id.product_id.property_stock_production.id,
                    'raw_material_production_id': self.id,
                    'company_id': self.company_id.id,
                    'price_unit': line_id.product_id.standard_price,
                    'procure_method': 'make_to_stock',
                    'origin': self.name,
                    'warehouse_id': source_location.get_warehouse().id,
                    'group_id': self.procurement_group_id.id,
                    'propagate': self.propagate,
                    'suggest_qty': line_id.product_qty,
                    'move_order_type': 'manufacturing_picking',
                }
                moves.create(data)

        else:
            for bom_line, line_data in exploded_lines:
                _logger.warning("bom bom_line, %d/%d" % (bom_line.id, bom_line.bom_id.id))

                moves += self._generate_raw_move(bom_line, line_data)
        return moves
