# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def create_reorder_rule(self, min_qty=0.0, max_qty=0.0, qty_multiple=1.0, overwrite=False):
        swo_obj = self.env['stock.warehouse.orderpoint']
        for rec in self:
            rec.product_tmpl_id.sale_ok = True
            rec.product_tmpl_id.purchase_ok = False
            rec.product_tmpl_id.product_ll_type = "finished"
            rec.product_tmpl_id.order_ll_type = "ordering"
            rec.product_tmpl_id.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id,
                                                     self.env.ref('stock.route_warehouse0_mto').id])]
            reorder_rules = swo_obj.search([('product_id', '=', rec.id)])
            reorder_rules.unlink()
            continue
            reorder_vals = {
                'product_id': rec.id,
                'product_min_qty': min_qty,
                'product_max_qty': max_qty,
                'qty_multiple': qty_multiple,
                'active': True,
                'product_uom': rec.uom_id.id,
            }

            if rec.type in ('product', 'consu') and not reorder_rules:
                self.env['stock.warehouse.orderpoint'].create(reorder_vals)
            elif rec.type in ('product', 'consu') and reorder_rules and overwrite:
                for reorder_rule in reorder_rules:
                    reorder_rule.write(reorder_vals)


class CreateOrderPointWizard(models.TransientModel):
    _name = "create.order.point"

    def action_create_in_aboard_rule(self):
        # products = self.env["product.product"].search([("inner_spec", "!=", False)])
        # products = self.env["product.product"].search(
        #         ['|', ("default_code", "=ilike", "99.%"), ("default_code", "=ilike", "98.%")])

        products = self.env["product.product"].search(
                [("default_code", "=ilike", "98.%")])

        products.create_reorder_rule()

    def action_combine_purchase_order(self):
        pos = self.env["purchase.order"].search([("state", "=", "make_by_mrp")])
        same_origin = {}
        for po in pos:
            if len(po.order_line) > 1:
                continue
            if po.order_line[0].product_id.id in same_origin.keys():
                same_origin[po.order_line[0].product_id.id].append(po)
            else:
                same_origin[po.order_line[0].product_id.id] = [po]

        for key in same_origin.keys():
            po_group = same_origin[key]
            total_qty = 0
            procurements = self.env["procurement.order"]
            for po in po_group:
                total_qty += po.order_line[0].product_qty
                procurements += po.order_line[0].procurement_ids

            # 生成薪的po单 在po0的基础上
            po_group[0].order_line[0].product_qty = total_qty
            po_group[0].order_line[0].procurement_ids = procurements

            for po in po_group[1:]:
                po.button_cancel()
