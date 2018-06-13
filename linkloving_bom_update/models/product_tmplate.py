# -*- coding: utf-8 -*-
import json
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MultiApplyBom(models.Model):
    _name = 'multi.apply.bom'

    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        product_ts = self.env['product.template'].search([('id', 'in', active_ids)])
        product_ts.apply_bom_update()


class MrpProductionExtend(models.Model):
    _inherit = 'mrp.production'

    is_bom_update = fields.Boolean()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def bom_update(self):
        if not self.bom_ids:
            raise UserError(u'该产品没有BOM')
        return {
            'type': 'ir.actions.client',
            'tag': 'bom_update',
            'bom_id': self.bom_ids[0].id
        }

    @api.multi
    def apply_bom_update(self):
        for product_t in self:
            if product_t.bom_ids:
                bom_id = product_t.bom_ids[0]
            else:
                raise UserError(u"%s 没有Bom" % (product_t.name))

            mos = self.env["mrp.production"].search(
                [('bom_id', '=', bom_id.id), ('state', 'not in', ['cancel', 'done'])])
            procurement_to_op = self.env["procurement.order"]
            for mo in mos:
                if mo.state in ['draft', 'confirmed', 'waiting_material']:
                    mo.action_cancel()
                    if mo.procurement_ids.move_dest_id.procurement_id:  # 订单制
                        mo.procurement_ids.cancel()
                        mo.procurement_ids.move_dest_id.procurement_id.cancel()
                        mo.procurement_ids.move_dest_id.procurement_id.reset_to_confirmed()
                        procurement_to_op += mo.procurement_ids.move_dest_id.procurement_id
                        # mo.procurement_ids.move_dest_id.procurement_id.run()
                    elif mo.procurement_ids:
                        procurement_to_op += mo.procurement_ids
                        # mo.procurement_ids.run()
                    else:
                        new_mo = mo.copy()
                        new_mo.state = "draft"
                elif mo.state in ['prepare_material_ing', 'finish_prepare_material', 'already_picking', 'progress',
                                  'waiting_inspection_finish', 'waiting_rework', 'waiting_inventory_material',
                                  'waiting_warehouse_inspection', 'waiting_post_inventory']:
                    mo.is_bom_update = True
            if procurement_to_op:
                procurement_to_op.run()
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"应用成功",
                "text": u"已应用成功",
                "sticky": False
            }
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def bom_update(self):
        if not self.self.product_tmpl_id.bom_ids:
            raise UserError(u'该产品没有BOM')
        return {
            'type': 'ir.actions.client',
            'tag': 'bom_update',
            'bom_id': self.product_tmpl_id.bom_ids[0].id
        }

    # 由于选bom表的时候的bug 暂支取消
    # @api.multi
    # def write(self, vals):
    #     if 'RT-ENG' in self.name and not self.env.user.has_group('mrp.group_mrp_manager'):
    #         raise UserError(u'只有库存管理员才可以修改基础物料')
    #     return super(ProductProduct, self).write(vals)

    @api.multi
    def unlink(self):
        for product in self:
            if 'RT-ENG' in product.name and not self.env.user.has_group('mrp.group_mrp_manager'):
                raise UserError(u'只有库存管理员才可以删除基础物料')
        return super(ProductProduct, self).unlink()

    @api.model
    def create(self, vals):
        if 'name' in vals and 'RT-ENG' in vals['name'] and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以创建基础物料')
        return super(ProductProduct, self).create(vals)

    def apply_bom_update(self):
        for product in self:
            bom_id = product.product_tmpl_id.bom_ids[0]
            mos = self.env["mrp.production"].search(
                [('bom_id', '=', bom_id.id), ('state', 'not in', ['cancel', 'done'])])
            procurement_to_op = self.env["procurement.order"]
            for mo in mos:
                if mo.state in ['draft', 'confirmed', 'waiting_material']:
                    mo.action_cancel()
                    if mo.procurement_ids.move_dest_id.procurement_id:  # 订单制
                        mo.procurement_ids.cancel()
                        mo.procurement_ids.move_dest_id.procurement_id.cancel()
                        mo.procurement_ids.move_dest_id.procurement_id.reset_to_confirmed()
                        procurement_to_op += mo.procurement_ids.move_dest_id.procurement_id
                        # mo.procurement_ids.move_dest_id.procurement_id.run()
                    elif mo.procurement_ids:
                        procurement_to_op += mo.procurement_ids
                        # mo.procurement_ids.run()
                    else:
                        new_mo = mo.copy()
                        new_mo.state = "draft"
                elif mo.state in ['prepare_material_ing', 'finish_prepare_material', 'already_picking', 'progress',
                                  'waiting_inspection_finish', 'waiting_rework', 'waiting_inventory_material',
                                  'waiting_warehouse_inspection', 'waiting_post_inventory']:
                    mo.is_bom_update = True
            if procurement_to_op:
                procurement_to_op.run()
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"应用成功",
                "text": u"已应用成功",
                "sticky": False
            }
        }
