# -*- coding: utf-8 -*-
import json
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def bom_detail(self):

        return {
            'type': 'ir.actions.client',
            'tag': 'bom_update',
            'bom_id': self.id
        }

    def get_bom(self):
        res = []
        for line in self.bom_line_ids:
            res.append(self.get_bom_line(line))
        result = {
            'uuid': str(uuid.uuid1()),
            'bom_id': self.id,
            'product_id': self.product_tmpl_id.id,
            'product_tmpl_id': self.product_tmpl_id.id,
            'name': self.product_tmpl_id.name,
            'code': self.product_tmpl_id.default_code,
            'process_id': self.process_id.name,
            'bom_ids': res
        }

        return result

    def get_bom_line(self, line, level=0):
        bom_line_ids = []
        if line.child_line_ids:
            if level < 6:
                level += 1
            for l in line.child_line_ids:
                bom_line_ids.append(_get_rec(l, level))
            if level > 0 and level < 6:
                level -= 1
        bom_id = line.product_id.product_tmpl_id.bom_ids
        process_id = False
        if bom_id:
            process_id = bom_id[0].process_id.name

        res = {
            'name': line.product_id.name,
            'product_id': line.product_id.id,
            'product_tmpl_id': line.product_id.product_tmpl_id.id,
            'is_highlight': line.is_highlight,
            'id': line.id,
            'product_specs': line.product_id.product_specs,
            'code': line.product_id.default_code,
            'uuid': str(uuid.uuid1()),
            'qty': line.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': bom_line_ids
        }

        return res


def _get_rec(object, level, qty=1.0, uom=False):
    for l in object:
        bom_line_ids = []
        if l.child_line_ids:
            if level < 6:
                level += 1
            for line in l.child_line_ids:
                bom_line_ids.append(_get_rec(line, level))
            if level > 0 and level < 6:
                level -= 1
        bom_id = l.product_id.product_tmpl_id.bom_ids
        process_id = False
        if bom_id:
            process_id = bom_id[0].process_id.name
        res = {
            'name': l.product_id.name,
            'product_id': l.product_id.id,
            'product_tmpl_id': l.product_id.product_tmpl_id.id,
            'code': l.product_id.default_code,
            'uuid': str(uuid.uuid1()),
            'product_specs': l.product_id.product_specs,
            'is_highlight': l.is_highlight,
            'id': l.id,
            'qty': l.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': bom_line_ids
        }

    return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    is_highlight = fields.Boolean()

    @api.multi
    def write(self, vals):
        if 'RT-ENG' in self.bom_id.product_tmpl_id.name and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以修改基础bom')
        return super(MrpBomLine, self).write(vals)

    @api.multi
    def unlink(self):
        if 'RT-ENG' in self.bom_id.product_tmpl_id.name and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'只有库存管理员才可以修改基础bom')
        return super(MrpBomLine, self).unlink()

    @api.model
    def create(self, vals):
        if 'bom_id' in vals:
            product_name = self.env['mrp.bom'].browse(vals['bom_id']).product_tmpl_id.name
            if 'RT-ENG' in product_name and not self.env.user.has_group('mrp.group_mrp_manager'):
                raise UserError(u'只有库存管理员才可以修改基础bom')
        return super(MrpBomLine, self).create(vals)

    @api.multi
    def toggle_highlight(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        for record in self:
            record.is_highlight = not record.is_highlight



            # def update_bom_line(self, line_id, postfix, product_id, products):
            #     bom = line_id.bom_id
            #     product_tmpl_id = bom.product_tmpl_id
            #     default_code = get_next_default_code(product_tmpl_id.default_code)
            #     new_name = product_tmpl_id.name + postfix
            #     if products.get(line_id):
            #         new_bom_id = products.get(line_id).get('new_bom_id')
            #         new_product_tmpl_id = products.get(line_id).get('new_product_tmpl_id')
            #     else:
            #         new_product_tmpl_id = product_tmpl_id.copy(name=new_name)
            #         new_bom_id = bom.copy(product_tmpl_id=new_product_tmpl_id, default_code=default_code)
            #         products.update({
            #             line_id: {
            #                 'new_bom_id': new_bom_id,
            #                 'new_product_id': new_product_tmpl_id,
            #             }
            #         })
            #         self.create({
            #             'product_id': product_id,
            #             'bom_id': new_bom_id.id
            #         })
            #     return new_product_tmpl_id


def get_next_default_code(default_code):
    if not default_code:
        raise UserError(u'产品没有对应料号')

    version = default_code.split('.')[-1]

    return int(version) + 1
