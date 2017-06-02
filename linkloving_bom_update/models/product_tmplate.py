# -*- coding: utf-8 -*-
import json
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def write(self, vals):
        if 'RT-ENG' in vals['name'] and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以修改基础物料')
        return super(ProductTemplate, self).write(vals)

    @api.multi
    def unlink(self):
        if 'RT-ENG' in self.name and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以删除基础物料')
        return super(ProductTemplate, self).unlink()

    @api.model
    def create(self, vals):
        if 'RT-ENG' in vals['name'] and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以创建基础物料')
        return super(ProductTemplate, self).create(vals)

    @api.multi
    def bom_update(self):
        if not self.bom_ids:
            raise UserError(u'该产品没有BOM')
        return {
            'type': 'ir.actions.client',
            'tag': 'bom_update',
            'bom_id': self.bom_ids[0].id
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

    @api.multi
    def write(self, vals):
        if 'RT-ENG' in self.bom_id.product_tmpl_id.name and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以修改基础物料')
        return super(ProductProduct, self).write(vals)

    @api.multi
    def unlink(self):
        if 'RT-ENG' in self.name and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以删除基础物料')
        return super(ProductProduct, self).unlink()

    @api.model
    def create(self, vals):
        if 'RT-ENG' in vals['name'] and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以创建基础物料')
        return super(ProductProduct, self).create(vals)
