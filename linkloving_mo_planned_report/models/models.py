# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

MO_FIELDS = ['name', 'product_id', 'date_planned_start', 'date_planned_finished', 'product_qty', 'qty_unpost',
             'origin_sale_id', 'state']


class PlannedDetailReport(models.Model):
    _name = 'planned.detail.report'
    """
    排产情况记录, 便于采购查看
    """
    name = fields.Char(string=u'名称', require=True)
    sale_ids = fields.Many2many(string=u'销售订单', comodel_name="sale.order",
                                domain=[('state', 'not in', ['cancel', 'draft'])])

    def action_view_detail_report(self):
        if not self.sale_ids:
            raise UserError(u'请选择销售订单')
        # report = self.env["mo.planned.report"].sudo().create({
        #     'sale_ids': [6, 0, self.sale_ids.ids]
        # })
        return self.action_view_report()

    # class MoPlannedReport(models.TransientModel):
    #     _name = 'mo.planned.report'
    #
    #     sale_ids = fields.Many2many(comodel_name="sale.order", string=u"销售单", domain=[('state', 'not in', ['cancel', 'draft'])])

    def action_view_report(self):
        vals = self._prepare_report_vals()
        return {
            'name': self.name,
            'type': 'ir.actions.client',
            'tag': 'mo_planned_report',
            'context': {"vals": vals}
        }

    def get_related_mos(self, line_mo, mos):
        MP = self.env["mrp.production"].sudo()
        global relate_mos
        relate_mos = self.env["mrp.production"].sudo()

        def reci_relate_mos(line_mo):
            origin_name = line_mo.name
            global relate_mos
            relate_mos += line_mo
            while mos.filtered(lambda x: origin_name in x.origin if origin_name else False):
                mo = mos.filtered(lambda x: origin_name == x.origin.split(':')[1])
                for mo1 in mo:
                    reci_relate_mos(mo1)
                else:
                    return

        reci_relate_mos(line_mo)

        return relate_mos

    def selection_mapped(self, selection_list, state):
        for sel in selection_list:
            if state == sel[0]:
                return sel[1]

    def get_purchase_product(self, product):
        if product.purchase_ok and self.env.ref("purchase.route_warehouse0_buy") in product.route_ids:
            return product

        def reci_bom_po(product):
            product_can_pruchase = self.env["product.product"].sudo()
            boms, lines = product.bom_ids[0].explode(product, 1)
            for bom_line, data in lines:
                sub_product = bom_line.product_id
                if sub_product.purchase_ok and self.env.ref("purchase.route_warehouse0_buy") in sub_product.route_ids:
                    product_can_pruchase += sub_product
                else:
                    if sub_product.bom_count > 0:
                        product_can_pruchase += reci_bom_po(sub_product)

            return product_can_pruchase

        all_can_purchase_product = reci_bom_po(product)
        return all_can_purchase_product

    def _prepare_report_vals(self):
        # process_ids = self.env["mrp.process"].sudo().search([])
        # mrp_production = self.env["mrp.production"].sudo()
        vals = []
        # mos = mrp_production.search([('origin_sale_id', 'in', self.sale_ids.ids)])
        # finished_product_mos = self.env["mrp.production"]
        index = 1
        for sale in self.sale_ids:
            for line in sale.order_line:
                all_can_purchase_product = self.get_purchase_product(line.product_id)

                # line_mo = mos.filtered(
                #     lambda x: x.origin_sale_id == sale and line.product_id == x.product_id)  # 对应这个订单行的MO号

                product_vals = []
                for purchase_product in all_can_purchase_product:
                    po_lines = self.env["purchase.order.line"].sudo().search([('product_id', '=', purchase_product.id)])

                    pos_vals = []
                    for po_line in po_lines.filtered(lambda x: x.order_id.state not in ['cancel']):
                        pos_vals.append({
                            'id': po_line.order_id.id,
                            'name': po_line.order_id.name,
                            'handle_date': po_line.order_id.handle_date,
                            'state': self.selection_mapped(po_line.order_id._fields.get("state").selection,
                                                           po_line.order_id.state),
                            'product_name': po_line.product_id.display_name,
                            # 'qty_available': po_line.product_id.qty_available,
                            # 'virtual_available': po_line.product_id.virtual_available,
                            # 'incoming_qty': po_line.product_id.incoming_qty,
                            'product_qty': po_line.product_qty,
                            'qty_received': po_line.qty_received,
                        })

                    product_vals.append({
                        'name': purchase_product.display_name,
                        'qty_available': purchase_product.qty_available,
                        'virtual_available': purchase_product.virtual_available,
                        'incoming_qty': purchase_product.incoming_qty,
                        'outgoing': purchase_product.outgoing,
                        # 'state': self.selection_mapped(purchase_product._fields.get("state").selection, purchase_product.state),
                        'orders': pos_vals,
                    })

                vals.append({
                    'name': sale.name + '-' + str(index),
                    'validity_date': sale.validity_date or '',
                    'partner_name': sale.partner_id.name,
                    'pi_number': sale.pi_number or '',
                    'product_name': line.product_id.display_name,
                    'order_qty': line.product_qty,
                    'orders': product_vals,
                })
                index += 1

        return vals


class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def change_handle_date(self, vals):
        for po in self:
            if po.state in ["done", "cancel", "purchase"]:
                raise UserError(u"该单据已取消或者已下单,无法修改交期")
        return self.write(vals)
