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
PURCHASE_TYPE = {
    'draft': u'草稿',
    'to approve': u'待审核',
    'purchase': u'采购订单',
    'make_by_mrp': u'MRP生成'
}
MO_STATE = {
    'draft': u'草稿',
    'confirmed': u'已排产',
    'waiting_material': u'等待备料',
    'prepare_material_ing': u'备料中',
    'finish_prepare_material': u'备料完成',
    'already_picking': u'已领料',
    'planned': u'安排中',
    'progress': u'生产中',
    'waiting_quality_inspection': u'等待品检',
    'quality_inspection_ing': u'品检中',
    'waiting_rework': u'等待返工',
    'rework_ing': u'返工中',
    'waiting_inventory_material': u'等待清点退料',
    'waiting_warehouse_inspection': u'等待检验退料',
    'waiting_post_inventory': u'等待入库'
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_detail(self):
        bom_ids = self.bom_ids
        bom_lines = []
        process = False
        service = ''
        draft_qty = 0.0
        if self.order_ll_type == 'ordering':
            draft_qty = self.get_draft_po_qty(self.product_variant_ids[0])
            on_produce = self.incoming_qty
        elif self.order_ll_type == 'stock':
            draft_qty = self.get_draft_mo(self.id)
            on_produce = self.get_onproduct_mo(self.id)

        po_lines = self.env['purchase.order.line'].search(
            [('product_id', '=', self.product_variant_ids[0].id), ('state', 'not in', ['cancel', 'done'])])
        line_ids = []
        for line in po_lines:
            if line.product_qty > line.qty_received:
                line_ids.append({
                    'name': line.order_id.name,
                    'id': line.order_id.id,
                    'qty': line.product_qty,
                    'date_planned': line.date_planned,
                    'state': PURCHASE_TYPE[line.order_id.state]
                })

        mo_ids = self.env['mrp.production'].search(
            [('product_tmpl_id', '=', self.id), ('state', 'not in', ['cancel', 'done']),
             ])
        ids = []
        if mo_ids:
            for mo in mo_ids:
                ids.append({
                    'id': mo.id,
                    'name': mo.name,
                    'qty': mo.product_qty,
                    'state': MO_STATE[mo.state],
                    'date': mo.date_planned_start,
                    # 'origin': mo.origin if mo.origin else '',
                })

        if bom_ids:
            bom = bom_ids[0]
            lines = bom.bom_line_ids
            process = bom.process_id.name

            for line in lines:
                line_process = False
                has_purchase = has_mo = False
                # FIXME:
                line_draft_qty = line_on_produce = 0.0

                if line.product_id.order_ll_type == 'ordering':
                    line_draft_qty = self.get_draft_po_qty(line.product_id.product_variant_ids[0])
                    line_on_produce = line.product_id.incoming_qty
                    has_purchase = True
                elif line.product_id.order_ll_type == 'stock':
                    line_draft_qty = self.get_draft_mo(line.product_id.product_tmpl_id.id)

                    line_on_produce = self.get_onproduct_mo(line.product_id.product_tmpl_id.id)
                    if line_draft_qty or line_on_produce:
                        has_mo = True
                bom_ids = line.product_id.bom_ids
                if bom_ids:
                    line_process = bom_ids[0].process_id.name
                res = {}
                level = False
                # purchase_line_ids = self.env['purchase.order.line'].search(
                #     [('product_id', '=', line.product_id.id), ('state', 'not in', ['cancel', 'done'])])
                # for purchase_line in purchase_line_ids:
                #     if purchase_line.product_qty > purchase_line.qty_received:
                #         has_purchase = True
                if line.product_id.bom_ids or has_purchase or has_mo:
                    level = True
                res.update({
                    'product_id': line.product_id.product_tmpl_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'level': level,
                    'product_qty': line.product_qty,
                    'process': line_process,
                    'type': PRODUCT_TYPE.get(line.product_id.product_ll_type),
                    'service': line.product_id.order_ll_type,
                    'on_produce': line_on_produce,
                    'draft': line_draft_qty,
                    'stock': line.product_id.qty_available,
                    'require': line.product_id.outgoing_qty

                })
                bom_lines.append(res)
        return {
            'name': self.name,
            'bom_lines': bom_lines,
            'product_id': self.id,
            'process': process,
            'type': PRODUCT_TYPE.get(self.product_ll_type),
            'service': line.product_id.order_ll_type,
            'mo_ids': ids,
            'po_lines': line_ids,
            'on_produce': on_produce,
            'draft': draft_qty,
            'stock': self.qty_available,
            'require': self.outgoing_qty
        }

    def get_draft_po_qty(self, product_id):
        pos = self.env["purchase.order"].search([("state", "in", ("make_by_mrp", "draft"))])
        chose_po_lines = self.env["purchase.order.line"]
        total_draft_order_qty = 0
        for po in pos:
            for po_line in po.order_line:
                if po_line.product_id.id == product_id.id:
                    chose_po_lines += po_line
                    total_draft_order_qty += po_line.product_qty
        return total_draft_order_qty

    def get_draft_mo(self, product_id):
        mo_ids = self.env['mrp.production'].search([('product_tmpl_id', '=', product_id), ('state', '=', 'draft')])
        return sum(mo.product_qty for mo in mo_ids)

    def get_onproduct_mo(self, product_id):
        mo_ids = self.env['mrp.production'].search(
            [('product_tmpl_id', '=', product_id), ('state', 'not in', ['draft', 'cancel', 'done'])])
        return sum(mo.product_qty for mo in mo_ids)

    @api.multi
    def show_detail(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'product_detail',
            'product_id': self.id
        }

    class ProductTemplate(models.Model):
        _inherit = 'product.product'

        @api.multi
        def show_detail(self):
            return {
                'type': 'ir.actions.client',
                'tag': 'product_detail',
                'product_id': self.product_tmpl_id.id
            }
