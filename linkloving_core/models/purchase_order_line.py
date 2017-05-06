# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api
from models import MO_STATE
import uuid


# MO_STATE = {
#     'draft': u'草稿',
#     'confirmed': u'已排产',
#     'waiting_material': u'等待备料',
#     'prepare_material_ing': u'备料中',
#     'finish_prepare_material': u'备料完成',
#     'already_picking': u'已领料',
#     'planned': u'安排中',
#     'progress': u'生产中',
#     'waiting_quality_inspection': u'等待品检',
#     'quality_inspection_ing': u'品检中',
#     'waiting_rework': u'等待返工',
#     'rework_ing': u'返工中',
#     'waiting_inventory_material': u'等待清点退料',
#     'waiting_warehouse_inspection': u'等待检验退料',
#     'waiting_post_inventory': u'等待入库'
# }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def show_product_detail(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'product_detail',
            'product_id': self.product_id.product_tmpl_id.id
        }

    @api.multi
    def get_mo_list(self):

        for line in self:
            origin = line.order_id.origin
            sources = []
            res = []
            if origin:
                mos = origin.split(',')

                for mo in mos:
                    mo_ids = mo.split(':')
                    for mo_id in mo_ids:
                        sources.append(mo_id.strip())
            for s in set(sources):
                if s.startswith('MO'):
                    mo_id = self.env['mrp.production'].search([('name', '=', s)])
                    for move_line in mo_id.sim_stock_move_lines:
                        print line.product_id.id
                        print move_line.product_id.id
                        if line.product_id.id == move_line.product_id.id:
                            res.append({
                                'name': mo_id.name,
                                'product_qty': move_line.product_uom_qty,
                                'product_id': mo_id.product_tmpl_id.product_variant_ids[0].id,
                                'date': mo_id.date_planned_start,
                                'state': MO_STATE[mo_id.state],
                                'id': mo_id.id,
                                'model': "mrp.production",
                                'origin': mo_id.origin
                            })
                else:
                    so_id = self.env['sale.order'].search([('name', '=', s)])
                    for order_line_id in so_id.order_line:
                        if line.product_id == order_line_id.product_id:
                            res.append({
                                'partner_name': so_id.partner_id.name,
                                'name': so_id.name,
                                'id': so_id.id,
                                'model': 'sale.order',
                                'origin': False,
                                'product_qty': order_line_id.product_qty,
                                'date': so_id.validity_date,
                            })
            return res

    @api.model
    def get_source_list(self, origin, product_id):
        sources = []
        res = []
        if origin:
            mos = origin.split(',')

            for mo in mos:
                mo_ids = mo.split(':')
                for mo_id in mo_ids:
                    sources.append(mo_id.strip())
            for s in set(sources):
                if s.startswith('MO'):
                    mo_id = self.env['mrp.production'].search([('name', '=', s)])
                    for move_line in mo_id.sim_stock_move_lines:
                        print move_line.product_id.id
                        print product_id
                        if product_id == move_line.product_id.id:
                            res.append({
                                'name': mo_id.name,
                                'product_qty': move_line.product_uom_qty,
                                'product_id': mo_id.product_tmpl_id.product_variant_ids[0].id,
                                'date': mo_id.date_planned_start,
                                'state': MO_STATE[mo_id.state],
                                'uuid': uuid.uuid1(),
                                'id': mo_id.id,
                                'model': "mrp.production",
                                'origin': mo_id.origin
                            })
                elif s.startswith('SO'):
                    so_id = self.env['sale.order'].search([('name', '=', s)])
                    for order_line_id in so_id.order_line:
                        if product_id == order_line_id.product_id.id:
                            res.append({
                                'partner_name': so_id.partner_id.name,
                                'name': so_id.name,
                                'id': so_id.id,
                                'model': 'sale.order',
                                'origin': False,
                                'state': so_id.state,
                                'product_qty': order_line_id.product_qty,
                                'date': so_id.validity_date,
                            })

            return res
