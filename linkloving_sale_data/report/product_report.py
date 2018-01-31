# -*- coding: utf-8 -*-

import simplejson
from datetime import datetime
import xlwt
import StringIO
from pprint import pprint

from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request


class ProductProductReport(http.Controller):
    @http.route(['/report/linkloving_sale_data.product_report'], type='http', auth='user',
                multilang=True)
    def product_report(self, **data):

        data = simplejson.loads(data['options'])
        if data:
            xls = StringIO.StringIO()
            xls_wookbook = xlwt.Workbook()
            data_sheet = xls_wookbook.add_sheet('data')

            style = xlwt.easyxf(
                'font: height 250;'
                'alignment: vert center, horizontal center;'
                'borders: left thin, right thin, top thin, bottom thin;'
            )

            header_style = xlwt.easyxf(
                'font: height 250, bold True;'
                'borders: left thin, right thin, top thin, bottom thin;'
                'align: vertical center, horizontal center;'
            )

            header_list = [
                u'产品', u'数量'
            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            print data, 'sssss'
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('name') and vals.get('name') or '',
                                 style)
                data_sheet.write(current_row, 1, vals.get('qty') and vals.get('qty') or 0, style)

                if not record.get('line'):
                    current_row += 1
                    continue
                i = 0
                for line in record.get('line').itervalues():

                    if i > 0:
                        data_sheet.write(current_row, 0,
                                         vals.get('name') and vals.get('name') or '', style)
                        data_sheet.write(current_row, 1, vals.get('partner') and vals.get('partner') or '', style)
                        data_sheet.write(current_row, 2, vals.get('date_order') and vals.get('date_order') or '', style)
                    data_sheet.write(current_row, 3, line.get('name') and line.get('name') or '', style)
                    data_sheet.write(current_row, 4, line.get('product_specs') and line.get('product_specs') or '',
                                     style)
                    data_sheet.write(current_row, 5, line.get('price_unit') and line.get('price_unit') or '',
                                     style)
                    data_sheet.write(current_row, 6, line.get('quantity') and line.get('quantity') or '', style)
                    data_sheet.write(current_row, 7, line.get('qty_received') and line.get('qty_received') or '', style)

                    current_row += 1
                    i += 1

            for x, i in enumerate([2, 2, 2, 2, 3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]):
                data_sheet.col(x).width = 2560 * i

            for x in range(0, row):
                data_sheet.row(x).height_mismatch = 1
                data_sheet.row(x).height = 500

            xls_wookbook.save(xls)
            xls.seek(0)
            content = xls.read()
            return request.make_response(content, headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=products.xls;')
            ])
        else:
            raise UserError(_('Error!'), _('These are no records no this period.'))
