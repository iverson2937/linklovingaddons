# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

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

    def action_unreserved_stock_picking(self):
        pickings = self.env["stock.picking"].search([("state", "in", ["partially_available", "assigned"]),
                                                     ("picking_type_code", "=", "outgoing")])
        pickings.do_unreserve()

    def action_create_menu(self):
        menus = self.env["product.category"].search([])
        menus.menu_create()

    def action_handle_stock_move(self):
        moves = self.env["stock.move"].search([('id', 'in',
                                                [347132, 347037, 347061, 347076, 347185, 347031, 347032, 347033, 347034,
                                                 347035, 347036, 347038, 347039, 347040, 347041, 347042, 347043, 347044,
                                                 347045, 347046, 347047, 347048, 347049, 347050, 347051, 347052, 347053,
                                                 347054, 347055, 347057, 347058, 347059, 347060, 347062, 347063, 347064,
                                                 347065, 347066, 347056, 347067, 347068, 347069, 347070, 347071, 347072,
                                                 347073, 347074, 347075, 347077, 347078, 347079, 347080, 347081, 347082,
                                                 347083, 347084, 347085, 347086, 347087, 347088, 347089, 347090, 347091,
                                                 347092, 347093, 347094, 347095, 347096, 347097, 347098, 347099, 347100,
                                                 347101, 347102, 347103, 347104, 347105, 347106, 347107, 347108, 347109,
                                                 347110, 347111, 347112, 347113, 347114, 347115, 347116, 347117, 347118,
                                                 347119, 347120, 347121, 347122, 347123, 347124, 347125, 347126, 347127,
                                                 347128, 347129, 347130, 347131, 347133, 347134, 347135, 347136, 347137,
                                                 347138, 347139, 347140, 347141, 347142, 347143, 347144, 347145, 347146,
                                                 347147, 347148, 347149, 347150, 347151, 347152, 347153, 347154, 347155,
                                                 347156, 347157, 347158, 347159, 347160, 347161, 347162, 347163, 347164,
                                                 347166, 347170, 347165, 347167, 347168, 347169, 347171, 347172, 347173,
                                                 347174, 347175, 347176, 347177, 347178, 347179, 347180, 347181, 347182,
                                                 347183, 347184, 347186, 347187, 347188, 347189, 347190, 347191, 347192,
                                                 347193, 347194, 347195, 347196, 347197, 347198, 347199, 347200, 347201,
                                                 347202, 347203, 347204, 347205, 347206, 347207, 347208, 347209, 347210,
                                                 347211, 347212, 347213, 347214, 347215, 347216])])
        moves.action_cancel()
        print(111111)

    def action_cancel_mo(self):
        productions = self.env["mrp.production"].search([('state', 'in', ['draft', 'confirmed'])])
        productions.action_cancel()

    def action_cancel_so(self):
        # sos_unlink = self.env["sale.order"].search([('state', '=', 'cancel')])
        # sos_unlink.unlink()

        sos = self.env["sale.order"].search([('state', '=', 'sale'),
                                             ('shipping_rate', '<=', '0')])
        i = 0
        # self.order_line.mapped('procurement_ids')
        # filtered(lambda order: order.state != 'done')
        # procurement.rule_id.action == 'manufacture'
        so_cancel_redo = self.env["sale.order"]
        for so in sos:
            mos = self.env["mrp.production"].search([('origin', 'like', so.name)])
            if all(mo.state in ["draft", "confirmed", "cancel"] for mo in mos):
                so.temp_no = True
                # so_cancel_redo += so

    def cancel_temp_no(self):
        so_cancel_redo = self.env["sale.order"].search([("temp_no", "=", True)], limit=10)
        for so in so_cancel_redo:
            i = i + 1
            _logger.warning("start doing so, %d/%d" % (i, len(so_cancel_redo)))
            try:
                so.action_cancel()

                # sos = self.env["sale.order"].search([('state', '=', 'cancel')])
                so.action_draft()
                so.action_confirm()
                so.temp_no = False
            except:
                continue
    def action_confirm_canceled_so(self):
        pass
        # sos = self.env["sale.order"].search([('state', '=', 'cancel')])
        # sos.action_draft()
        # sos.action_confirm()


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    temp_no = fields.Boolean()
