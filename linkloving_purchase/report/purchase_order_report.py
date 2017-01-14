# -*- coding: utf-8 -*-

import simplejson
from datetime import datetime
import xlwt
import StringIO
from pprint import pprint

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class report_purchase(http.Controller):
    @http.route(['/report/linkloving_purchase.report_purchase'], type='http', auth='user', multilang=True)
    def report_purchase(self, **data):
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
                u'采购单号', u'供应商', u'创建人', u'单据日期', u'产品',
                u'材料编码', u'规格描述', u'单价', u'合同数', u'入库数',
                u'合同金额', u'总合同金额', u'已报销金额', u'已付款金额'

            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('name') and vals.get('name') or '', style)
                data_sheet.write(current_row, 1, vals.get('partner') and vals.get('partner') or '', style)
                data_sheet.write(current_row, 2, vals.get('user_name') and vals.get('user_name') or '', style)
                data_sheet.write(current_row, 3, vals.get('date_order') and vals.get('date_order') or '', style)
                data_sheet.write(current_row, 10, vals.get('order_price') and vals.get('order_price') or '', style)

                if not record.get('line'):
                    current_row += 1
                    continue

                for line in record.get('line').itervalues():
                    data_sheet.write(current_row, 4, line.get('name') and line.get('name') or '', style)
                    data_sheet.write(current_row, 5, line.get('default_code') and line.get('default_code') or '', style)
                    data_sheet.write(current_row, 6, line.get('price_unit') and line.get('price_unit') or 0, style)
                    data_sheet.write(current_row, 7, line.get('quantity') and line.get('quantity') or 0, style)
                    data_sheet.write(current_row, 8, line.get('delivery_qty') and line.get('delivery_qty') or 0, style)
                    data_sheet.write(current_row, 9, line.get('order_price') and line.get('order_price') or 0, style)

                    current_row += 1

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
                ('Content-Disposition', 'attachment; filename=purchase_order_sum.xls;')
            ])
        else:
            raise UserError(u'错误!', u'该截至日期之前不存在使用订单')
