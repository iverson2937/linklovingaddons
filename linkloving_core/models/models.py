# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import uuid

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


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def action_combine(self, args, **kwargs):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        qty = 0
        product_id = []
        ids = []
        origin = []
        for record in self.env['mrp.production'].browse(args):
            if record.state not in ['draft', 'confirmed', 'waiting_material']:
                raise UserError(_("Only draft MO can combine."))

            product_id.append(record.product_id)
            ids.append(record.id)
            qty += record.product_qty
            if record.origin:
                origin.append(record.origin)
            record.action_cancel()

        if len(set(product_id)) > 1:
            raise UserError(_('MO product must be same'))
        bom_id = product_id[0].bom_ids
        mo_id = self.env['mrp.production'].create({
            'product_qty': qty,
            'product_id': product_id[0].id,
            'bom_id': bom_id.id,
            'product_uom_id': product_id[0].uom_id.id,
            'state': 'draft',
            'origin': ','.join(origin),
            'process_id': bom_id.process_id.id,
            'unit_price': bom_id.process_id.unit_price,
            'hour_price': bom_id.hour_price,
            'in_charge_id': bom_id.process_id.partner_id.id,
        })
        mo_id.source_mo_ids = ids

        return {
            'name': mo_id.name,
            'qty': mo_id.product_qty,
            'id': mo_id.id,
            'product_id': mo_id.product_tmpl_id.id,
            'date_planned_start': mo_id.date_planned_start,
            'state': mo_id.state,
            'status_light': mo_id.status_light,
            'material_light': mo_id.material_light,
        }

    @api.multi
    def get_detail(self):
        if not self.product_variant_ids:
            raise UserError(u'已归档无法查看')
        bom_ids = self.bom_ids
        bom_lines = []
        process = False
        state_bom = False
        service = ''
        draft_qty = on_produce = 0.0
        if self.product_ll_type == 'raw material':
            draft_qty = self.get_draft_po_qty(self.product_variant_ids[0])
            on_produce = self.incoming_qty
        else:
            draft_qty = self.get_draft_mo(self.id)
            on_produce = self.get_onproduct_mo(self.id)

        po_lines = self.env['purchase.order.line'].sudo().search(
            [('product_id', '=', self.product_variant_ids[0].id), ('state', 'not in', ['cancel', 'done'])])
        line_ids = []
        for line in po_lines:
            if line.product_qty > line.qty_received:
                line_ids.append({
                    'name': line.order_id.name,
                    'id': line.order_id.id,
                    'line_id': line.id,
                    'origin': line.order_id.origin,
                    'qty': line.product_qty,
                    'date_planned': line.date_planned,
                    'state': PURCHASE_TYPE[line.order_id.state],
                    'status_light': line.order_id.status_light,
                    'remark': line.order_id.remark if line.order_id.remark else ''
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
                    'prepare_material_state': mo.prepare_material_state,
                    'material_state': mo.material_state,
                    'product_id': mo.product_tmpl_id.product_variant_ids[0].id,
                    'qty': mo.product_qty,
                    'uuid': str(uuid.uuid1()),
                    'origin': mo.origin if mo.origin else '',
                    'date_planned_finished': mo.date_planned_finished if mo.date_planned_finished else '',
                    'date_planned_start': mo.date_planned_start if mo.date_planned_start else '',
                    'planned_start_backup': mo.planned_start_backup if mo.planned_start_backup else '',
                    'in_charge_id': mo.in_charge_id.name,
                    'state': mo.state,
                    # 'status_light': mo.status_light,
                    # 'material_light': mo.material_light,
                    'remark': mo.remark if mo.remark else ''
                    # 'origin': mo.origin if mo.origin else '',
                })

        if bom_ids:
            bom = bom_ids[0]
            state_bom = bom.state
            lines = bom.bom_line_ids
            process = bom.process_id.name

            res = {}

            for line in lines:
                has_purchase = has_mo = level = line_process = False
                # FIXME:
                line_draft_qty = line_on_produce = 0.0

                if line.product_id.purchase_ok:
                    if line.product_id.product_variant_ids:
                        line_draft_qty = self.get_draft_po_qty(line.product_id.product_variant_ids[0])
                    line_on_produce = line.product_id.incoming_qty
                else:
                    line_draft_qty = self.get_draft_mo(line.product_id.product_tmpl_id.id)

                    line_on_produce = self.get_onproduct_mo(line.product_id.product_tmpl_id.id)
                    if line_draft_qty or line_on_produce:
                        has_mo = True
                bom_ids = line.product_id.bom_ids
                state_bom_line = False
                if bom_ids:
                    line_process = bom_ids[0].process_id.name
                    state_bom_line = bom_ids[0].state

                res = {}
                level = False
                # purchase_line_ids = self.env['purchase.order.line'].search(
                #     [('product_id', '=', line.product_id.id), ('state', 'not in', ['cancel', 'done'])])
                # for purchase_line in purchase_line_ids:
                #     if purchase_line.product_qty > purchase_line.qty_received:
                #         has_purchase = True
                if line.product_id.bom_ids or line.product_id.purchase_ok or has_mo:
                    level = True
                res.update({
                    'product_id': line.product_id.product_tmpl_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'level': level,
                    'product_qty': line.product_qty,
                    'process': line_process,
                    'type': PRODUCT_TYPE.get(line.product_id.product_ll_type),
                    'part_no': line.product_id.default_code,
                    'service': line.product_id.order_ll_type,
                    'on_produce': line_on_produce,
                    'draft': line_draft_qty,
                    'state_bom': state_bom_line,
                    'purchase_ok': line.product_id.purchase_ok,
                    'stock': line.product_id.qty_available,
                    'require': line.product_id.outgoing_qty,
                })
                bom_lines.append(res)
        bom_lines.sort(key=lambda k: (k.get('type', 0)))
        return {
            'name': self.name,
            'bom_lines': bom_lines,
            'product_id': self.id,
            'product_p_id': self.product_variant_ids[0].id,
            'process': process,
            'type': PRODUCT_TYPE.get(self.product_ll_type),
            'part_no': self.default_code,
            'service': self.order_ll_type,
            'mo_ids': ids,
            'po_lines': line_ids,
            'on_produce': on_produce,
            'draft': draft_qty,
            'purchase_ok': self.purchase_ok,
            'stock': self.qty_available,
            'require': self.outgoing_qty,
            'state_bom': state_bom
        }

    @api.multi
    def cost_detail(self):
        return {
            'name': '成本明细',
            'type': 'ir.actions.client',
            'tag': 'cost_detail',
            'product_id': self.id
        }

    @api.multi
    def get_cost(self):
        if not self.product_variant_ids:
            raise UserError(u'已归档无法查看')
        bom_ids = self.bom_ids
        bom_lines = []
        process = False
        state_bom = False

        if bom_ids:
            bom = bom_ids[0]
            state_bom = bom.state
            lines = bom.bom_line_ids
            process = bom.process_id.name

            res = {}

            for line in lines:
                bom_ids = line.product_id.bom_ids
                if bom_ids:
                    line_process = bom_ids[0].process_id.name
                    state_bom_line = bom_ids[0].state
                res = {}
                level = False
                if line.product_id.bom_ids:
                    level = True

                total_cost = line.product_id.pre_cost_cal()
                material_cost = line.product_id.get_material_cost()
                man_cost = total_cost - material_cost
                res.update({
                    'product_id': line.product_id.product_tmpl_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'level': level,
                    'type': PRODUCT_TYPE.get(line.product_id.product_ll_type),
                    'product_qty': line.product_qty,
                    'part_no': line.product_id.default_code,
                    'service': line.product_id.order_ll_type,
                    'man_cost': man_cost,
                    'material_cost': material_cost,
                    'total_cost': total_cost

                })
                bom_lines.append(res)
        bom_lines.sort(key=lambda k: (k.get('type', 0)))
        total_cost = self.product_variant_ids[0].pre_cost_cal()
        mateial_cost = self.product_variant_ids[0].get_material_cost()
        man_cost = total_cost - mateial_cost
        return {
            'name': self.name,
            'bom_lines': bom_lines,
            'product_id': self.id,
            'product_p_id': self.product_variant_ids[0].id,
            'process': process,
            'type': PRODUCT_TYPE.get(self.product_ll_type),
            'part_no': self.default_code,
            'service': self.order_ll_type,
            'state_bom': state_bom,
            'man_cost': man_cost,
            'material_cost': mateial_cost,
            'total_cost': total_cost
        }

    def get_draft_po_qty(self, product_id):
        pos = self.env["purchase.order"].sudo().search([("state", "in", ("make_by_mrp", "draft", "to approve"))])
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
        return sum(mo.on_produce_qty for mo in mo_ids)

    @api.multi
    def show_detail(self):
        return {
            'name': '产品详细',
            'type': 'ir.actions.client',
            'tag': 'product_detail',
            'product_id': self.id
        }

    class ProductTemplate(models.Model):
        _inherit = 'product.product'

        @api.multi
        def cost_detail(self):
            return {
                'name': '成本明细',
                'type': 'ir.actions.client',
                'tag': 'cost_detail',
                'product_id': self.product_tmpl_id.id
            }

        @api.multi
        def show_detail(self):
            return {
                'name': '产品详细',
                'type': 'ir.actions.client',
                'tag': 'product_detail',
                'product_id': self.product_tmpl_id.id
            }

        @api.multi
        def get_material_cost(self):
            bom_obj = self.env['mrp.bom']
            for product in self:
                bom = bom_obj._bom_find(product=product)
                if bom:
                    material_cost = 0.0
                    for line in bom.bom_line_ids:
                        material_cost += line.product_id.pre_cost_cal()
                    return material_cost
                else:
                    return product.get_highest_purchase_price()
