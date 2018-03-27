# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, SUPERUSER_ID
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
            raw_material_approve_id = self.env['ir.values'].sudo().get_default(
                'stock.config.settings', 'raw_material_approve_id')
            finished_material_approve_id = self.env['ir.values'].sudo().get_default(
                'stock.config.settings', 'finished_material_approve_id')
            if s.state == 'confirm' and len(
                    types) > 1 and 'raw material' in types and raw_material_approve_id != finished_material_approve_id:
                raise UserError('原材料制成品不能同时盘点')
            elif len(types) == 1 and types[0] == 'raw material' and s.state == 'confirm':

                if not raw_material_approve_id:
                    raise UserError('请联系管理员设置员材料库存调整审核人')
                s.to_approve_id = raw_material_approve_id
            elif s.state == 'confirm':

                if not finished_material_approve_id:
                    raise UserError('请设置制成品库存调整审核人')
                s.to_approve_id = finished_material_approve_id
            # 奇葩需求奇葩代码
            wood = []
            kb = self.env['product.category'].search([('name', '=', 'KB卡板制程品')])
            if kb:
                wood.append(kb.id)
            mc = self.env['product.category'].search([('name', '=', '10木板原材料')])
            if mc:
                wood.append(mc.id)
            if s.state == 'confirm' and wood:
                categ_ids = s.mapped('line_ids.product_id.categ_id')

                wood_material_approve_id = self.env['ir.values'].sudo().get_default(
                    'stock.config.settings', 'wood_material_approve_id')
                if not wood_material_approve_id:
                    raise UserError('请设置木材库存调整审核人')
                if any(c.id in wood for c in categ_ids):
                    s.to_approve_id = wood_material_approve_id

    @api.multi
    def _compute_can_approve(self):
        for i in self:
            if self._uid == SUPERUSER_ID:

                i.can_approve = True
            elif i.to_approve_id == self.env.user:
                i.can_approve = True
            else:
                i.can_approve = False
