# -*- coding: utf-8 -*-
import json
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    review_id = fields.Many2one("review.process",
                                string=u'待...审核',
                                track_visibility='always',
                                readonly=True, copy=False)

    @api.multi
    def bom_detail(self):

        return {
            'type': 'ir.actions.client',
            'tag': 'new_bom_update',
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
            'product_specs': self.product_tmpl_id.product_specs,
            'name': self.product_tmpl_id.name,
            'code': self.product_tmpl_id.default_code,
            'process_id': self.process_id.name,
            'bom_ids': res,
            'state': self.state,
            'review_line': self.review_id.get_review_line_list(),
        }

        return result

    def get_bom_line(self, line, level=0):
        bom_line_ids = []
        if line.child_line_ids:
            if level < 6:
                level += 1
            for l in line.child_line_ids:
                bom_line_ids.append(_get_rec(l, level, line))
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
            'parent_id': line.bom_id.id,
            'product_specs': line.product_id.product_specs,
            'code': line.product_id.default_code,
            'uuid': str(uuid.uuid1()),
            'qty': line.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': bom_line_ids
        }

        return res


def _get_rec(object, level, parnet, qty=1.0, uom=False):
    for l in object:
        bom_line_ids = []
        if l.child_line_ids:
            if level < 6:
                level += 1
            for line in l.child_line_ids:
                bom_line_ids.append(_get_rec(line, level, parnet))
            if level > 0 and level < 6:
                level -= 1
        bom_id = l.product_id.product_tmpl_id.bom_ids
        process_id = False
        parent_id = False
        if bom_id:

            process_id = bom_id[0].process_id.name
            print bom_id[0].bom_line_ids
            parent_bom_id = l.bom_id.product_tmpl_id.bom_ids[0]
            print bom_id.product_tmpl_id.name
            print l.bom_id.product_tmpl_id.name
            for bom_line in parent_bom_id.bom_line_ids:
                print bom_line.product_id, 'dd'
                print l.bom_id.product_tmpl_id.product_variant_ids[0], 'ww'
                if bom_line.product_id.id == l.bom_id.product_tmpl_id.product_variant_ids[0].id:
                    parent_id = bom_line.id

        res = {
            'name': l.product_id.name,
            'product_id': l.product_id.id,
            'product_tmpl_id': l.product_id.product_tmpl_id.id,
            'code': l.product_id.default_code,
            'product_specs': l.product_id.product_specs,
            'is_highlight': l.is_highlight,
            'id': l.id,
            'parent_id': parnet.id,
            'qty': l.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': bom_line_ids
        }

    return res