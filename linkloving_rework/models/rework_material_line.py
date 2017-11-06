# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ReworkMaterialLine(models.Model):
    _name = 'rework.material.line'

    def _get_default_product_uom_id(self):
        return self.env['product.uom'].search([], limit=1, order='id').id

    mo_id = fields.Many2one('mrp.production', on_delete="cascade")

    product_id = fields.Many2one(
        'product.product', 'Product', required=True)
    product_qty = fields.Float(
        'Product Quantity', default=1.0,
        digits=dp.get_precision('Product Unit of Measure'), required=True)
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure',
        default=_get_default_product_uom_id,
        oldname='product_uom', required=True,
        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")

    _sql_constraints = [
        ('bom_qty_zero', 'CHECK (product_qty>0)', 'All product quantities must be greater than 0.\n'
                                                  'You should install the mrp_byproduct module if you want to manage extra products on BoMs !'),
    ]

    @api.multi
    def write(self, vals):
        if vals.get('product_qty'):
            if self.mo_id.state not in ('draft', 'confirmed', 'waiting_material'):
                raise UserError('已经在领料中,不能修改数量')
            stock_moves = self.mo_id.move_raw_ids.filtered(lambda x: x.product_id.id == self.product_id.id)
            if stock_moves:
                if len(stock_moves) > 1:
                    raise UserError('超过一个出库项目,请联系管理员')
                stock_moves.product_uom_qty = vals.get('product_qty')
            else:
                raise UserError('没有相关联的出库项目,请联系管理员')

        return super(ReworkMaterialLine, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(ReworkMaterialLine, self).create(vals)
        if res.mo_id.move_raw_ids:
            raise UserError('已经生产库存移动单，不能再添加返工条目，请取消重新再下')
        return res
