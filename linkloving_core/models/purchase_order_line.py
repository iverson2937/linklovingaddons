# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api


class SaleOrderLine(models.Model):
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
            if origin:
                mos = origin.split(',')

                for mo in mos:
                    mo_ids = mo.split(':')
                    for mo_id in mo_ids:
                        sources.append(mo_id.strip())
