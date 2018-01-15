# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockInventoryInherit(models.Model):
    _inherit = 'stock.inventory'
    to_approve_id = fields.Many2one('res.users', compute='_to_approve_id', store=True)
    can_approve = fields.Boolean(compute='_compute_can_approve')

    @api.depends('line_ids')
    def _to_approve_id(self):
        for s in self:
            product_ll_types = s.mapped('line_ids.product_id.product_ll_type')
            types = list(set(product_ll_types))
            if len(types) > 1 and 'raw material' in types:
                pass
            elif len(types) == 1 and types[0] == 'raw material':
                raw_material_approve_id = self.env['ir.values'].sudo().get_default(
                    'stock.config.settings', 'raw_material_approve_id')
                if not raw_material_approve_id:
                    raise UserError('请联系管理员设置员材料库存调整审核人')
                s.to_approve_id = raw_material_approve_id
            else:
                finished_material_approve_id = self.env['ir.values'].sudo().get_default(
                    'stock.config.settings', 'finished_material_approve_id')
                if not finished_material_approve_id:
                    raise UserError('请设置制成品库存调整审核人')
                s.to_approve_id = finished_material_approve_id

    @api.multi
    def _compute_can_approve(self):
        for i in self:
            if i.to_approve_id == self.env.user:
                return True
            else:
                return False
