# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api

dict = {
    'Buy': u'采购',
    'Make To Order': u'按订单生成',
    'Manufacture': u'制造'
}

PRODUCT_TYPE = {
    'raw material': u'原料',
    'semi-finished': u'半成品',
    'finished': u'成品',
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_detail(self):
        bom_ids = self.bom_ids
        bom_lines = []
        process = False
        service = ''
        if self.route_ids:
            for route in self.route_ids:
                service += dict[route.name] + ','
        po_lines = self.env['purchase.order.line'].search(
            [('product_id', '=', self.product_variant_ids[0].id), ('state', 'not in', ['cancel'])])
        line_ids = []
        for line in po_lines:
            line_ids.append({
                'name': line.order_id.name,
                'id': line.order_id.id,
                'qty': line.product_qty,
            })

        mo_ids = self.env['mrp.production'].search(
            [('product_tmpl_id', '=', self.id), ('state', 'not in', ['cancel', 'done'])])
        ids = []
        if mo_ids:
            for mo in mo_ids:
                ids.append({
                    'id': mo.id,
                    'name': mo.name,
                    'qty': mo.product_qty,
                    'state': mo.state,
                    'date': mo.date_planned_start,
                    'origin': mo.origin if mo.origin else '',
                })

        if bom_ids:
            bom = bom_ids[0]
            lines = bom.bom_line_ids
            process = bom.process_id.name

            for line in lines:
                res = {}
                level = False
                if line.product_id.bom_ids or self.env['purchase.order.line'].search(
                        [('product_id', '=', line.product_id.id), ('state', 'not in', ['cancel'])]):
                    level = True
                res.update({
                    'product_id': line.product_id.product_tmpl_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'level': level,
                    'product_qty': line.product_qty
                })
                bom_lines.append(res)

        return {
            'name': self.name,
            'bom_lines': bom_lines,
            'product_id': self.id,
            'process': process,
            'type': PRODUCT_TYPE.get(self.product_ll_type),
            'service': service,
            'mo_ids': ids,
            'po_lines': line_ids
        }
