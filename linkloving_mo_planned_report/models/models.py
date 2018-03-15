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

    def _prepare_report_vals(self):
        process_ids = self.env["mrp.process"].sudo().search([])
        mrp_production = self.env["mrp.production"].sudo()
        vals = []
        mos = mrp_production.search([('origin_sale_id', 'in', self.sale_ids.ids)])
        finished_product_mos = self.env["mrp.production"]
        index = 1
        for sale in self.sale_ids:
            for line in sale.order_line:
                line_mo = mos.filtered(
                    lambda x: x.origin_sale_id == sale and line.product_id == x.product_id)  # 对应这个订单行的MO号
                related_mos = self.get_related_mos(line_mo, mos)
                orders = related_mos.read(fields=MO_FIELDS)
                mos_vals = []
                for mo_order in related_mos:
                    pos = self.env["purchase.order"].sudo().search([('state', 'not in', ['done', 'cancel', 'purchase']),
                                                                    ('origin', 'like', mo_order.name)])

                    pos_vals = []
                    for po_line in pos.mapped("order_line"):
                        pos_vals.append({
                            'id': po_line.order_id.id,
                            'name': po_line.order_id.name,
                            'handle_date': po_line.order_id.handle_date,
                            'state': self.selection_mapped(po_line.order_id._fields.get("state").selection,
                                                           po_line.order_id.state),
                            'product_name': po_line.product_id.display_name,
                            'qty_available': po_line.product_id.qty_available,
                            'virtual_available': po_line.product_id.virtual_available,
                            'incoming_qty': po_line.product_id.incoming_qty,
                            'product_qty': po_line.product_qty,
                        })

                    mos_vals.append({
                        'name': mo_order.name,
                        'state': self.selection_mapped(mo_order._fields.get("state").selection, mo_order.state),

                        'product_name': mo_order.product_id.display_name,
                        'process_name': mo_order.process_id.name or '',
                        'date_planned_finished': mo_order.date_planned_finished,
                        'product_qty': mo_order.product_qty,
                        'orders': pos_vals,
                    })

                vals.append({
                    'name': sale.name + '-' + str(index),
                    'validity_date': sale.validity_date or '',
                    'partner_name': sale.partner_id.name,
                    'pi_number': sale.pi_number or '',
                    'order_qty': line.product_qty,
                    'orders': mos_vals,
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
