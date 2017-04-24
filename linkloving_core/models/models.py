# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_detail(self):
        product_id = self.env['product.template'].browse(45964)
        bom_ids = product_id.bom_ids
        bom_lines = []

        if bom_ids:
            lines = bom_ids[0].bom_line_ids
            for line in lines:
                res = {}
                res.update({
                    'name': line.product_id.name,
                    'product_qty': line.product_qty
                })
            bom_lines.append(res)

        return {
            'name': product_id.name,
            'bom_lines': bom_lines
        }
