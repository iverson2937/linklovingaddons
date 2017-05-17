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
            'name': self.product_tmpl_id.name_get()[0][1],
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

        res = {
            'name': line.product_id.name_get()[0][1],
            'product_id': line.product_id.default_code,
            'id': line.id,
            'code': line.product_id.default_code,
            'uuid': str(uuid.uuid1()),
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

        res = {
            'name': l.product_id.name_get()[0][1],
            'product_id': l.product_id.default_code,
            'code': l.product_id.default_code,
            'uuid': str(uuid.uuid1()),
            'id': l.id,
            'level': level,
            'bom_ids': bom_line_ids
        }

    return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.model
    def bom_line_update(self, vals, is_update=False, bom_id=False):
        parents = vals.get('parents')
        bom_obj = self.env['mrp.bom']
        postfix = u'新版本'
        bom_id = self.env['mrp.bom'].browse(bom_id)
        products = {}
        bom_ids = []
        temp_product_id = False

        if not is_update:
            new_main_product_templ_id = bom_id.product_tmpl_id.copy(name=postfix)
            new_main_bom_id = bom_id.copy(product_templ_id=new_main_product_templ_id)

            for val in vals:
                product_id = val.get('product_id')
                to_update_bom_line_ids = val.get('parents')
                # to_update_bom_line_ids = parents[:-1]
                for line in to_update_bom_line_ids:
                    line_id = self.env['mrp.bom.line'].browse(line)
                    new_product_tmpl_id = line_id.product_id.product_tmpl_id.copy()
                    new_bom_id = line_id.bom_id.copy()
                    if not line_id:
                        bom_id = self.env['mrp.bom'].browse(line)
                        new_product_tmpl_id = bom_id.product_tmpl_id.copy()
                        new_bom_id = bom_id.copy()
                    if product_id:
                        self.create({
                            'product_id': product_id,
                            'bom_id': new_bom_id.id,
                        })
                        product_id = False
                    self.update_bom_line_copy(new_bom_id, temp_product_id, line_id.product_id)
                    temp_product_id = new_product_tmpl_id.id

    @staticmethod
    def update_bom_line_copy(new_bom_id, new_product_id, old_product_id):
        if new_product_id:
            for line in new_bom_id.bom_line_ids:
                if line.product_id.id == old_product_id:
                    line.product_id = new_product_id

    def update_bom_line(self, line_id, postfix, product_id, products):
        bom = line_id.bom_id
        product_tmpl_id = bom.product_tmpl_id
        default_code = get_next_default_code(product_tmpl_id.default_code)
        new_name = product_tmpl_id.name + postfix
        if products.get(line_id):
            new_bom_id = products.get(line_id).get('new_bom_id')
            new_product_tmpl_id = products.get(line_id).get('new_product_tmpl_id')
        else:
            new_product_tmpl_id = product_tmpl_id.copy(name=new_name)
            new_bom_id = bom.copy(product_tmpl_id=new_product_tmpl_id, default_code=default_code)
            products.update({
                line_id: {
                    'new_bom_id': new_bom_id,
                    'new_product_id': new_product_tmpl_id,
                }
            })
            self.create({
                'product_id': product_id,
                'bom_id': new_bom_id.id
            })
        return new_product_tmpl_id


def get_next_default_code(default_code):
    if not default_code:
        raise UserError(u'产品没有对应料号')

    version = default_code.split('.')[-1]

    return int(version) + 1


if __name__ == '__main__':
    get_next_default_code('123.444')
    abc = [1, 3, 4]
    efc = abc[:-1]
    efc[1:]
