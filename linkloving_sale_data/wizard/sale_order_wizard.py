# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrderListPrintWizard(models.TransientModel):
    _name = 'sale.order.list.wizard'

    team_ids = fields.Many2many('crm.team', string='Sale Team', required=True,
                                default=lambda self: self.env['crm.team'].search([]))

    start_date = fields.Date(u'订单开始日期',
                             default=(datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1))
    end_date = fields.Date(u'订单截至日期', default=datetime.datetime.now())

    def _get_data_by_sale(self, date1, date2, team_ids):
        returnDict = {}
        sale_obj = self.env['sale.order']
        domain = []
        if team_ids:
            domain.append(('team_id', 'in', team_ids.ids))
        d1 = domain + [('state', '=', 'sale'),
                       ('date_order', '>=', date1), ('date_order', '<=', date2)]
        sale_orders = sale_obj.search(d1, order='date_order')

        sale_sequence = 1
        for sale_order in sale_orders:
            returnDict[sale_order.id] = {'data': {}, 'line': {}}
            print sale_order.invoiced_amount
            returnDict[sale_order.id]['data'] = {
                'sequence': sale_sequence,
                'name': sale_order.name,
                'partner': sale_order.partner_id.name,
                'create_uid': sale_order.create_uid.name,
                'date_order': sale_order.date_order,
                'amount_total': sale_order.amount_total,
                'invoiced_amount': sale_order.invoiced_amount,
                'remaining_amount': sale_order.remaining_amount,
                'shipped_amount': sale_order.shipped_amount,
                'pre_payment_amount': sale_order.pre_payment_amount
            }
            for line in sale_order.order_line:
                returnDict[sale_order.id]['line'].update({line.id: {
                    'name': line.product_id.name,
                    'default_code': line.product_id.default_code,
                    'price_unit': line.price_unit,
                    'product_specs': line.product_specs,
                    'quantity': line.product_qty,
                    'qty_received': line.qty_delivered,
                    'qty_invoiced': line.qty_invoiced,
                    'price_subtotal': line.price_subtotal,
                }})
        return returnDict

    @api.multi
    def print_report(self):
        for report in self:
            datas = self._get_data_by_sale(report.start_date, report.end_date, report.team_ids)
            report_name = 'linkloving_sale_data.sale_order_report'

            if not datas:
                raise UserError(u'没找到相关数据')

            return self.env['report'].get_action(self, report_name, datas)
