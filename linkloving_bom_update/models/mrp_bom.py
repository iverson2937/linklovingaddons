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
            'level': level,
            'bom_ids': bom_line_ids
        }

    return res
