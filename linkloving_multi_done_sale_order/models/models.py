# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

# class linkloving_multi_done_sale_order(models.Model):
#     _name = 'linkloving_multi_done_sale_order.linkloving_multi_done_sale_order'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
from odoo.exceptions import UserError


class multi_set_sale_order_done(models.TransientModel):
    _name = 'set.sale.done'

    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        orders = self.env['sale.order'].search([('id', 'in', active_ids)])
        for order in orders:
            if order.state == "draft" or order.invoice_status in ["to invoice", "invoiced"]:
                continue
            else:
                for picking in order.picking_ids:

                    picking.action_confirm()
                    picking.force_assign()
                    picking.do_transfer()
                    if picking.state == 'draft':
                        picking.action_confirm()
                        if picking.state != 'assigned':
                            picking.action_assign()
                            if picking.state != 'assigned':
                                raise UserError(_(
                                    "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
                    for pack in picking.pack_operation_ids:
                        if pack.product_qty > 0:
                            pack.write({'qty_done': pack.product_qty})
                        else:
                            pack.unlink()
                    picking.do_transfer()
                    picking.to_stock()
