# -*- coding: utf-8 -*-
import json
import datetime
import types

import jpush
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_compare, math, float_utils
from odoo.addons import decimal_precision as dp


class StockInventory(models.Model):
    _inherit = 'stock.inventory'
    # 添加库存原因
    reason = fields.Char(string=u'原因')


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _generate_moves(self):
        moves = self.env['stock.move']
        Quant = self.env['stock.quant']
        for line in self:
            if float_utils.float_compare(line.theoretical_qty, line.product_qty,
                                         precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            vals = {
                'name': _('INV:') + (line.inventory_id.name or ''),
                'product_id': line.product_id.id,
                'product_uom': line.product_uom_id.id,
                'date': line.inventory_id.date,
                'company_id': line.inventory_id.company_id.id,
                'inventory_id': line.inventory_id.id,
                'state': 'confirmed',
                'reason': line.inventory_id.reason,
                'restrict_lot_id': line.prod_lot_id.id,
                'restrict_partner_id': line.partner_id.id,
                'move_order_type': 'inventory_out' if diff > 0 else 'inventory_in',
                'quantity_adjusted_qty': line.product_qty,
            }
            if diff < 0:  # found more than expected
                vals['location_id'] = line.product_id.property_stock_inventory.id
                vals['location_dest_id'] = line.location_id.id
                vals['product_uom_qty'] = abs(diff)
            else:
                vals['location_id'] = line.location_id.id
                vals['location_dest_id'] = line.product_id.property_stock_inventory.id
                vals['product_uom_qty'] = diff
            move = moves.create(vals)

            if diff > 0:
                domain = [('qty', '>', 0.0), ('package_id', '=', line.package_id.id),
                          ('lot_id', '=', line.prod_lot_id.id), ('location_id', '=', line.location_id.id)]
                preferred_domain_list = [[('reservation_id', '=', False)],
                                         [('reservation_id.inventory_id', '!=', line.inventory_id.id)]]
                quants = Quant.quants_get_preferred_domain(move.product_qty, move, domain=domain,
                                                           preferred_domain_list=preferred_domain_list)
                Quant.quants_reserve(quants, move)
            elif line.package_id:
                move.action_done()
                move.quant_ids.write({'package_id': line.package_id.id})
                quants = Quant.search([('qty', '<', 0.0), ('product_id', '=', move.product_id.id),
                                       ('location_id', '=', move.location_dest_id.id), ('package_id', '!=', False)],
                                      limit=1)
                if quants:
                    for quant in move.quant_ids:
                        if quant.location_id.id == move.location_dest_id.id:  # To avoid we take a quant that was reconcile already
                            quant._quant_reconcile_negative(move)
        return moves
