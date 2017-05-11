# -*- coding: utf-8 -*-
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
            print line
            print line
            res.append(self.get_bom_line(line))
        return {
            'uuid': str(uuid.uuid1()),
            'product_id': self.product_tmpl_id.id,
            'name': self.product_tmpl_id.name_get()[0][1],
            'bom_ids': res
        }

    def get_bom_line(self, object, level=0):
        result = []

        def _get_rec(object, level, qty=1.0, uom=False):
            for l in object:
                res = {}
                res['name'] = l.product_id.name_get()[0][1]
                res['product_id'] = l.product_id.id
                res['code'] = l.product_id.default_code
                res['uuid'] = str(uuid.uuid1())
                res['level'] = level
                result.append(res)
                if l.child_line_ids:
                    if level < 6:
                        level += 1
                    _get_rec(l.child_line_ids, level)
                    if level > 0 and level < 6:
                        level -= 1
            print result
            return result

        children = _get_rec(object, level)

        return children
