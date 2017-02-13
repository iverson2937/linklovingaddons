# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _


class PurchaseOrderListPrintWizard(models.TransientModel):
    _name = 'sale.order.list.wizard'

    team_ids = fields.Many2many('crm.team', string='Sale Team', required=True,
                                   default=lambda self: self.env['crm.team'].search([]))

    start_date = fields.Date(u'订单开始日期',
                             default=(datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1))
    end_date = fields.Date(u'订单截至日期', default=datetime.datetime.now())

    def _get_data_by_purchase(self, date1, date2):
        returnDict = {}
        sale_obj = self.env['sale.order']

        sale_orders = sale_obj.search([
            ('state', '=', 'purchase'),
            ('date_order', '>=', date1), ('date_order', '<=', date2)], order='name desc')

        sale_sequence = 1
        for sale_order in sale_orders:
            returnDict[sale_order.id] = {'data': {}, 'line': {}}
            returnDict[sale_order.id]['data'] = {
                'sequence': sale_sequence,
                'name': sale_order.name,
                'partner': sale_order.partner_id.name,
                'create_uid': sale_order.create_uid.name,
                'date_order': sale_order.date_order,
                'order_price': sale_order.amount_total,
            }
            for line in sale_order.order_line:
                returnDict[sale_order.id]['line'].update({line.id: {
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
            return {
                'name': 'Go to website',
                'tag': 'petstore.homepage',
                'type': 'ir.actions.client',
                'context':{'sss':'sss'},
                'target': 'self',
                'url': '/sale_orders/'
            }
