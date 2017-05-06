# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api


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
                if s.startswith('mo'):
                    mo_id = self.env['mrp.production'].search([('name', '=', s)])
                    for move_line in mo_id.sim_stock_move_lines:
                        if line.product_id == move_line.product_id:
                            res.append({
                                'name': mo_id.name,
                                'product_qty': line.product_qty,
                                'date_planned_start': mo_id.date_planned_start,
                                'state': mo_id.state
                            })
                else:
                    so_id = self.env['mrp.production'].search([('name', '=', s)])
                    for order_line_id in so_id.order_line:
                        if line.product_id == order_line_id.product_id:
                            res.append({
                                'partner_name': so_id.partner_id.name,
                                'name': so_id.name,
                                'product_qty': order_line_id.product_qty,
                                'date': so_id.validity_date,
                            })
