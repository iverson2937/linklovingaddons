# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def create_reorder_rule(self, min_qty=0.0, max_qty=0.0, qty_multiple=1.0, overwrite=False):
        swo_obj = self.env['stock.warehouse.orderpoint']
        for rec in self:
            reorder_rules = swo_obj.search([('product_id', '=', rec.id)])
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
        products = self.env["product.product"].search(
                ['|', ("default_code", "=ilike", "99.%"), ("default_code", "=ilike", "98.%")])
        products.create_reorder_rule()


class CreateOrderPointWizard(models.TransientModel):
    _name = "create.order.point.one"

    def action_create_in_aboard_rule(self):
        products = self.env["product.product"].search([("default_code", "=like", "99.%")])
        products.create_reorder_rule()


class ProductTemplateExtend(models.Model):
    _inherit = "product.template"
