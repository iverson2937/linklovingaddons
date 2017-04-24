# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_detail(self):
        bom_ids = self.bom_ids
        bom_lines = []
        level = False
        mo_ids = []
        po_lines = []

        if bom_ids:
            lines = bom_ids[0].bom_line_ids
            for line in lines:
                res = {}
                res.update({
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_qty': line.product_qty
                })
            bom_lines.append(res)

        return json.dump({
            'name': self.name,
            'level': level,
            'bom_lines': bom_lines,
            'product_id': self.id,
        })
