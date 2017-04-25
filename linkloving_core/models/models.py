# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_detail(self):
        print self
        bom_ids = self.bom_ids
        bom_lines = []

        mo_ids = []
        po_lines = []

        if bom_ids:
            lines = bom_ids[0].bom_line_ids
            for line in lines:
                res = {}
                level = False
                if line.product_id.bom_ids:
                    level = True
                res.update({
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'level': level,
                    'product_qty': line.product_qty
                })
                bom_lines.append(res)

        return {
            'name': self.name,
            'bom_lines': bom_lines,
            'product_id': self.id,
        }
