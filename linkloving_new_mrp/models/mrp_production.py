# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class NewMrpProduction(models.Model):
    _inherit = 'mrp.production'
    is_multi_output = fields.Boolean(default=True)
    output_product_ids = fields.One2many('mrp.production.material', 'mo_id', domain=[('type', '=', 'output')])
    input_product_ids = fields.One2many('mrp.production.material', 'mo_id', domain=[('type', '=', 'input')])

    def _generate_raw_moves(self, exploded_lines):
        self.ensure_one()
        moves = self.env['stock.move']
        source_location = self.picking_type_id.default_location_src_id
        if self.is_multi_output:
            if not self.input_product_ids:
                raise UserError('请添加投入物料')
            for line_id in self.input_product_ids:
                data = {
                    'name': self.name,
                    'date': self.date_planned_start,
                    'product_id': line_id.product_id.id,
                    'product_uom_qty': line_id.product_qty * self.product_qty,
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
                    'suggest_qty': line_id.product_qty * self.product_qty,
                }
                moves.create(data)

        if self.is_rework:
            if not self.rework_material_line_ids:
                raise UserError(u'请添加重工物料')
            for line_id in self.rework_material_line_ids:
                data = {
                    'name': self.name,
                    'date': self.date_planned_start,
                    'product_id': line_id.product_id.id,
                    'product_uom_qty': line_id.product_qty * self.product_qty,
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
                    'suggest_qty': line_id.product_qty * self.product_qty,
                }
                moves.create(data)

        else:
            for bom_line, line_data in exploded_lines:
                moves += self._generate_raw_move(bom_line, line_data)
        return moves

    def create(self, vals):
        return super(NewMrpProduction, self).create(vals)


class MrpProductionMaterial(models.Model):
    _name = 'mrp.production.material'
    product_id = fields.Many2one('product.product', string=u'产品', required=True)
    mo_id = fields.Many2one('mrp.production')
    type = fields.Selection([
        ('input', '输入'),
        ('output', '输出')
    ])
