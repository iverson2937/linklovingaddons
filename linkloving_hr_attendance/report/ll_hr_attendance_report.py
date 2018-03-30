# -*- coding: utf-8 -*-

import simplejson
from datetime import datetime, timedelta
import xlwt
import StringIO
from pprint import pprint

from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request


class ReportHrAttendanceSheet(http.Controller):
    @http.route(['/report/linkloving_hr_attendance.ll_hr_attendance_report'], type='http', auth='user',
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

            header_arr = []
            date1 = datetime.strptime(data["0"]["start_date"], "%Y-%m-%d")
            date2 = datetime.strptime(data["0"]["end_date"], "%Y-%m-%d")
            header_arr.append(" ")
            header_arr.append(date1.strftime("%d"))
            for index in range(1,((date2-date1).days + 1)):
                header_arr.append((date1 + timedelta(days=index)).strftime("%d"))

            print header_arr

            header_list = header_arr

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            rows_arr = []
            rows_arr.append(" ")
            for record in data.itervalues():
                for index_now in range(0, ((date2 - date1).days + 2)):
                    rows_arr.append(" ")
                vals = record.get('data')
                # print vals.get('time_arr')
                for time in vals.get('time_arr'):
                    time_date = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                    inside = 0
                    for time_header_detail in header_list:
                        time_string = ""
                        if (time_date + timedelta(hours=8)).day > 9:
                            time_string = str((time_date + timedelta(hours=8)).day)
                        else:
                            time_string = "0" + str((time_date + timedelta(hours=8)).day)
                        if time_header_detail == time_string:
                            print time_header_detail
                            rows_arr[inside] = rows_arr[inside] + "\r\n" + (time_date + timedelta(hours=8)).strftime('%H:%M:%S')
                        inside = inside + 1

                data_sheet.write(current_row, 0, vals.get('employee_id') and vals.get('employee_id') or '',
                                 style)
                for time_index in range(1,len(rows_arr)):
                    data_sheet.write(current_row, time_index, rows_arr[time_index], style)

                rows_arr = []
                rows_arr.append(" ")
                if not record.get('line'):
                    current_row += 1
                    continue
                i = 0

            for x, i in enumerate([2, 2, 2, 2, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,2, 2, 2]):
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