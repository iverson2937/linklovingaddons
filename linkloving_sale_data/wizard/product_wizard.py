# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductProductListWizard(models.TransientModel):
    _name = 'product.product.list.wizard'

    start_date = fields.Date(u'Start Dare',
                             default=(datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1))
    end_date = fields.Date(u'End Date', default=datetime.datetime.now())

    report_type = fields.Selection([
        ('sale', '销售'),
        ('shipping', '出货'),
    ], default='sale')

    def _get_data_by_products(self, date1, date2):
        returnDict = {}
        products_obj = self.env['product.product']

        product_ids = products_obj.sudo().search([('sale_ok', '=', True), ('type', '!=', 'service')], order='categ_id')

        purchase_sequence = 1
        for product in product_ids:

            returnDict[product.id] = {'data': {}, 'line': {}}
            if self.report_type == 'sale':

                returnDict[product.id]['data'] = {
                    'sequence': purchase_sequence,
                    'name': product.name,
                    'category_name': product.categ_id.name,
                    'default_code': product.default_code,
                    'inner_code': product.inner_code,
                    'inner_spec': product.inner_spec,
                    'qty': product.count_amount(self.start_date, self.end_date)
                }
            elif self.report_type == 'shipping':
                returnDict[product.id]['data'] = {
                    'sequence': purchase_sequence,
                    'category_name': product.categ_id.name,
                    'default_code': product.default_code,
                    'inner_code': product.inner_code,
                    'inner_spec': product.inner_spec,
                    'name': product.name,
                    'qty': product.count_shipped_amount(self.start_date, self.end_date)
                }

        return returnDict

    @api.multi
    def print_report(self):
        for report in self:
            datas = self._get_data_by_products(report.start_date, report.end_date)
            report_name = 'linkloving_sale_data.product_report'

            return self.env['report'].get_action(self, report_name, datas)
