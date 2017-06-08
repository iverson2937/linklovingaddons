# -*- coding: utf-8 -*-

import simplejson
from datetime import datetime
import xlwt
import StringIO
from pprint import pprint

from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request


class ReportHrExpenseSheet(http.Controller):
    @http.route(['/report/linkloving_report.linkloving_hr_expense_sheet_report'], type='http', auth='user',
                multilang=True)
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
                u'支出日期', u'报销单号', u'部门', u'产品', u'费用说明', u'金额', u'人员'
            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('accounting_date') and vals.get('accounting_date') or '',
                                 style)
                data_sheet.write(current_row, 1, vals.get('expense_no') and vals.get('expense_no') or '', style)
                data_sheet.write(current_row, 2, vals.get('department') and vals.get('department') or '', style)

                if not record.get('line'):
                    current_row += 1
                    continue
                i = 0
                for line in record.get('line').itervalues():

                    if i > 0:
                        data_sheet.write(current_row, 0,
                                         vals.get('accounting_date') and vals.get('accounting_date') or '', style)
                        data_sheet.write(current_row, 1, vals.get('expense_no') and vals.get('expense_no') or '', style)
                        data_sheet.write(current_row, 2, vals.get('department') and vals.get('department') or '', style)
                    data_sheet.write(current_row, 3, line.get('product') and line.get('product') or '', style)
                    data_sheet.write(current_row, 4, line.get('name') and line.get('name') or '', style)
                    data_sheet.write(current_row, 5, line.get('employee') and line.get('employee') or '', style)
                    data_sheet.write(current_row, 6, line.get('total_amount') and line.get('total_amount') or '', style)
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
                ('Content-Disposition', 'attachment; filename=hr_expense_sheet_sum.xls;')
            ])
        else:
            raise UserError(_('Error!'), _('These are no records no this period.'))


class ReportPrepaymentOutgoing(http.Controller):
    @http.route(['/report/linkloving_report.pre_payment_report'], type='http', auth='user',
                multilang=True)
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
                u'支出日期', u'暂支单号', u'部门', u'说明', u'金额', u'人员',
            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('accounting_date') and vals.get('accounting_date') or '',
                                 style)
                data_sheet.write(current_row, 1, vals.get('expense_no') and vals.get('expense_no') or '', style)
                data_sheet.write(current_row, 2, vals.get('department') and vals.get('department') or '', style)

                if not record.get('line'):
                    current_row += 1
                    continue
                i = 0
                for line in record.get('line').itervalues():

                    if i > 0:
                        data_sheet.write(current_row, 0,
                                         vals.get('accounting_date') and vals.get('accounting_date') or '', style)
                        data_sheet.write(current_row, 1, vals.get('expense_no') and vals.get('expense_no') or '', style)
                        data_sheet.write(current_row, 2, vals.get('department') and vals.get('department') or '', style)
                    data_sheet.write(current_row, 3, line.get('product') and line.get('product') or '', style)
                    data_sheet.write(current_row, 4, line.get('name') and line.get('name') or '', style)
                    data_sheet.write(current_row, 5, line.get('employee') and line.get('employee') or '', style)
                    data_sheet.write(current_row, 6, line.get('total_amount') and line.get('total_amount') or '', style)
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
                ('Content-Disposition', 'attachment; filename=hr_expense_sheet_sum.xls;')
            ])
        else:
            raise UserError(_('Error!'), _('These are no records no this period.'))
