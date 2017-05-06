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
                if s.startswith('MO'):
                    mo_id = self.env['mrp.production'].search([('name', '=', s)])
                    for move_line in mo_id.sim_stock_move_lines:
                        print line.product_id.id
                        print move_line.product_id.id
                        if line.product_id.id == move_line.product_id.id:
                            res.append({
                                'name': mo_id.name,
                                'product_qty': move_line.product_uom_qty,
                                'date': mo_id.date_planned_start,
                                'state': mo_id.state,
                                'is_so': True,
                                'origin': mo_id.origin
                            })
                            print res
                else:
                    so_id = self.env['sale.order'].search([('name', '=', s)])
                    for order_line_id in so_id.order_line:
                        if line.product_id == order_line_id.product_id:
                            res.append({
                                'partner_name': so_id.partner_id.name,
                                'name': so_id.name,
                                'is_so': True,
                                'origin': so_id.origin,
                                'product_qty': order_line_id.product_qty,
                                'date': so_id.validity_date,
                            })
                        print res
            return res
