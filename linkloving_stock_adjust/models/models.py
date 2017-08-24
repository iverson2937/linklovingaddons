# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class StockTransfer(models.Model):
    _name = 'stock.transfer'
    name = fields.Char('名称')
    picking_type_id = fields.Many2one('')

    input_product_ids = fields.Many2one('input.product.line', domain=[('product_type', '=', 'input')])
    output_product_ids = fields.One2many('input.product.line', domain=[('product_type', '=', 'output')])

    @api.model
    def _get_default_picking_type(self):
        return self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            (
                'warehouse_id.company_id', 'in',
                [self.env.context.get('company_id', self.env.user.company_id.id), False])],
            limit=1).id

    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Picking Type',
        default=_get_default_picking_type, required=True)

    @api.multi
    def confirm(self):
        pass

    @api.multi
    def transfer(self):
        pass

    def _generate_raw_moves(self, exploded_lines):
        self.ensure_one()
        moves = self.env['stock.move']
        source_location = self.picking_type_id.default_location_src_id

        if not self.input_product_ids or not self.output_product_ids:
            raise UserError('请添加投入产出')
            input_product_ids = self.input_product_ids

        for line_id in input_product_ids:
            data = {
                'name': self.name,
                'date': self.date_planned_start,
                'product_id': line_id.product_id.id,
                'product_uom_qty': self.product_qty,
                'product_uom': line_id.product_id.uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': line_id.product_id.property_stock_production.id,
                'raw_material_production_id': self.id,
                'company_id': self.company_id.id,
                'price_unit': line_id.product_id.standard_price,
                'procure_method': 'make_to_stock',
                'origin': self.name,
                'warehouse_id': source_location.get_warehouse().id,
                'propagate': self.propagate,
            }
            moves.create(data)


class StockTransferLine(models.Model):
    transfer_id = fields.Many2one('stock.transfer', on_delete="cascade")
    product_id = fields.Many2one('product.product')
    product_qty = fields.Float(string=u'数量')
    product_type = fields.Selection([
        ('input', u'投入'),
        ('output', u'产出')
    ])
