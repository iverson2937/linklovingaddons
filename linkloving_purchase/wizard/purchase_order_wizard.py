# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _


class PurchaseOrderListPrintWizard(models.TransientModel):
    _name = 'purchase.order.list.wizard'

    start_date = fields.Date(u'Start Dare',
                             default=(datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1))
    end_date = fields.Date(u'End Date', default=datetime.datetime.now())

    def _get_data_by_purchase(self, date1, date2):
        returnDict = {}
        purchase_obj = self.env['purchase.order']
        purchase_line_pool = self.env['purchase.order.line']

        purchase_ids = purchase_obj.sudo().search([
            ('state', 'in', ['sent', 'to approve', 'purchase']),
            ('date_order', '>=', date1), ('date_order', '<=', date2)], order='name desc')

        purchase_sequence = 1
        for purchase in purchase_ids:
            returnDict[purchase.id] = {'data': {}, 'line': {}}
            returnDict[purchase.id]['data'] = {
                'sequence': purchase_sequence,
                'name': purchase.name,
                'partner': purchase.partner_id.name,
                'create_uid': purchase.create_uid.name,
                'date_order': purchase.date_order,
                'order_price': purchase.amount_total,
                'remaining_amount': purchase.remaining_amount,
                'invoiced_amount': purchase.invoiced_amount,
                'shipped_amount': purchase.shipped_amount,
                'pre_payment_amount': purchase.pre_payment_amount

            }
            for line in purchase.order_line:
                returnDict[purchase.id]['line'].update({line.id: {
                    'name': line.product_id.name,
                    'default_code': line.product_id.default_code,
                    'price_unit': line.price_unit,
                    'product_specs': line.product_specs,
                    'quantity': line.product_qty,
                    'qty_received': line.qty_received,
                    'qty_invoiced': line.qty_invoiced,
                    'price_subtotal': line.price_subtotal,
                }})
        return returnDict

    @api.multi
    def print_report(self):
        for report in self:
            datas = self._get_data_by_purchase(report.start_date, report.end_date)
            report_name = 'linkloving_purchase.report_purchase'

            return self.env['report'].get_action(self, report_name, datas)
