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
        # 报销单

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
                u'支出日期', u'报销单号', u'部门', u'产品', u'单价', u'数量', u'小计', u'费用说明', u'报销单金额', u'暂支单', u'人员', u'备注'
            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('accounting_date') and vals.get('accounting_date') or '',
                                 style)
                data_sheet.write(current_row, 1, vals.get('expense_no') and vals.get('expense_no') or '', style)
                data_sheet.write(current_row, 2, vals.get('department') and vals.get('department') or '', style)
                data_sheet.write(current_row, 8, vals.get('total_amount') and vals.get('total_amount') or '', style)

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
                    data_sheet.write(current_row, 4, line.get('unit_amount') and line.get('unit_amount') or '', style)
                    data_sheet.write(current_row, 5, line.get('quantity') and line.get('quantity') or '', style)
                    data_sheet.write(current_row, 6, line.get('total_amount') and line.get('total_amount') or '', style)
                    data_sheet.write(current_row, 7, line.get('name') and line.get('name') or '', style)

                    data_sheet.write(current_row, 9,
                                     line.get('payment_line_ids') and line.get('payment_line_ids') or '', style)
                    data_sheet.write(current_row, 10, line.get('employee') and line.get('employee') or '', style)
                    data_sheet.write(current_row, 11, line.get('remark') and line.get('remark') or '', style)

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
                data_sheet.write(current_row, 1, vals.get('name') and vals.get('name') or '', style)
                data_sheet.write(current_row, 2, vals.get('department') and vals.get('department') or '', style)
                data_sheet.write(current_row, 3, vals.get('remark') and vals.get('remark') or '', style)
                data_sheet.write(current_row, 4, vals.get('amount') and vals.get('amount') or '', style)
                data_sheet.write(current_row, 5, vals.get('employee') and vals.get('employee') or '', style)
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
                ('Content-Disposition', 'attachment; filename=zz_sum.xls;')
            ])
        else:
            raise UserError(_('Error!'), _('These are no records no this period.'))


class PrePaymentDeductReport(http.Controller):
    @http.route(['/report/linkloving_report.pre_payment_deduct_report'], type='http', auth='user',
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
                u'支出日期', u'部门', u'报销单号', u'明细', u'抵扣金额', u'人员', u'暂支单号', u'暂支金额', u'暂支余额'
            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('accounting_date') and vals.get('accounting_date') or '',
                                 style)
                data_sheet.write(current_row, 1, vals.get('department') and vals.get('department') or '', style)
                data_sheet.write(current_row, 5, vals.get('employee') and vals.get('employee') or '', style)

                data_sheet.write(current_row, 6, vals.get('name') and vals.get('name') or '', style)
                data_sheet.write(current_row, 7, vals.get('amount') and vals.get('amount') or '', style)
                data_sheet.write(current_row, 8,
                                 vals.get('pre_payment_reminding') and vals.get('pre_payment_reminding') or '0.00',
                                 style)
                if not record.get('line'):
                    data_sheet.write(current_row, 2, '', style)
                    data_sheet.write(current_row, 3, '', style)
                    data_sheet.write(current_row, 4, '', style)
                    current_row += 1

                    continue
                i = 0
                for line in record.get('line').itervalues():

                    if i > 0:
                        data_sheet.write(current_row, 0,
                                         vals.get('accounting_date') and vals.get('accounting_date') or '', style)
                        data_sheet.write(current_row, 1, vals.get('department') and vals.get('department') or '', style)
                    data_sheet.write(current_row, 2, line.get('expense_no') and line.get('expense_no') or '', style)
                    data_sheet.write(current_row, 3, line.get('name') and line.get('name') or '', style)
                    data_sheet.write(current_row, 4, line.get('amount') and line.get('amount') or '', style)
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
                ('Content-Disposition', 'attachment; filename=zz_cd_sum.xls;')
            ])
        else:
            raise UserError(_('Error!'), _('These are no records no this period.'))


class PurchasePaymentReport(http.Controller):
    @http.route(['/report/linkloving_report.purchase_payment_report'], type='http', auth='user',
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
                u'支出日期', u'单号', u'供应商', u'金额', u'操作人'
            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('receive_date') and vals.get('receive_date') or '',
                                 style)
                data_sheet.write(current_row, 1, vals.get('name') and vals.get('name') or '', style)
                data_sheet.write(current_row, 2, vals.get('supplier') and vals.get('supplier') or '', style)

                data_sheet.write(current_row, 3, vals.get('amount') and vals.get('amount') or '', style)
                data_sheet.write(current_row, 4, vals.get('create_uid') and vals.get('create_uid') or '', style)
                # data_sheet.write(current_row, 8,
                #                  vals.get('pre_payment_reminding') and vals.get('pre_payment_reminding') or '0.00',
                #                  style)
                if not record.get('line'):
                    current_row += 1

                    continue
                i = 0
                # for line in record.get('line').itervalues():
                #
                #     if i > 0:
                #         data_sheet.write(current_row, 0,
                #                          vals.get('accounting_date') and vals.get('accounting_date') or '', style)
                #         data_sheet.write(current_row, 1, vals.get('department') and vals.get('department') or '', style)
                #     data_sheet.write(current_row, 2, line.get('expense_no') and line.get('expense_no') or '', style)
                #     data_sheet.write(current_row, 3, line.get('name') and line.get('name') or '', style)
                #     data_sheet.write(current_row, 4, line.get('amount') and line.get('amount') or '', style)
                #     current_row += 1
                #     i += 1

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
                ('Content-Disposition', 'attachment; filename=fksq_sum.xls;')
            ])
        else:
            raise UserError(_('Error!'), _('These are no records no this period.'))


class SaleAccountPaymentReport(http.Controller):
    @http.route(['/report/linkloving_report.account_payment_income_report'], type='http', auth='user',
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
                u'到款日期', u'单号', u'收入账户', u'销售团队', u'客户', u'金额', u'业务员', u'备注'
            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('payment_date') and vals.get('payment_date') or '',
                                 style)
                data_sheet.write(current_row, 1, vals.get('name') and vals.get('name') or '', style)
                data_sheet.write(current_row, 2, vals.get('journal_id') and vals.get('journal_id') or '', style)
                data_sheet.write(current_row, 3, vals.get('team_id') and vals.get('team_id') or '', style)
                data_sheet.write(current_row, 4, vals.get('partner_id') and vals.get('partner_id') or '', style)
                data_sheet.write(current_row, 5, vals.get('amount') and vals.get('amount') or '', style)
                data_sheet.write(current_row, 6, vals.get('sale_man') and vals.get('sale_man') or '', style)
                data_sheet.write(current_row, 7, vals.get('remark') and vals.get('remark') or '', style)
                # data_sheet.write(current_row, 8,
                #                  vals.get('pre_payment_reminding') and vals.get('pre_payment_reminding') or '0.00',
                #                  style)
                if not record.get('line'):
                    current_row += 1

                    continue
                i = 0
                # for line in record.get('line').itervalues():
                #
                #     if i > 0:
                #         data_sheet.write(current_row, 0,
                #                          vals.get('accounting_date') and vals.get('accounting_date') or '', style)
                #         data_sheet.write(current_row, 1, vals.get('department') and vals.get('department') or '', style)
                #     data_sheet.write(current_row, 2, line.get('expense_no') and line.get('expense_no') or '', style)
                #     data_sheet.write(current_row, 3, line.get('name') and line.get('name') or '', style)
                #     data_sheet.write(current_row, 4, line.get('amount') and line.get('amount') or '', style)
                #     current_row += 1
                #     i += 1

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
                ('Content-Disposition', 'attachment; filename=account_payment.xls;')
            ])
        else:
            raise UserError(_('Error!'), _('These are no records no this period.'))


# class AccountPaymentReportIncmoing(http.Controller):
#     @http.route(['/report/linkloving_report.account_payment_income_report'], type='http', auth='user',
#                 multilang=True)
#     def report_purchase(self, **data):
#
#         data = simplejson.loads(data['options'])
#         if data:
#             xls = StringIO.StringIO()
#             xls_wookbook = xlwt.Workbook()
#             data_sheet = xls_wookbook.add_sheet('data')
#
#             style = xlwt.easyxf(
#                 'font: height 250;'
#                 'alignment: vert center, horizontal center;'
#                 'borders: left thin, right thin, top thin, bottom thin;'
#             )
#
#             header_style = xlwt.easyxf(
#                 'font: height 250, bold True;'
#                 'borders: left thin, right thin, top thin, bottom thin;'
#                 'align: vertical center, horizontal center;'
#             )
#
#             header_list = [
#                 u'支出日期', u'单号', u'供应商', u'金额', u'操作人'
#             ]
#
#             [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]
#
#             current_row = 1
#             for record in data.itervalues():
#                 vals = record.get('data')
#
#                 data_sheet.write(current_row, 0, vals.get('receive_date') and vals.get('receive_date') or '',
#                                  style)
#                 data_sheet.write(current_row, 1, vals.get('name') and vals.get('name') or '', style)
#                 data_sheet.write(current_row, 2, vals.get('supplier') and vals.get('supplier') or '', style)
#
#                 data_sheet.write(current_row, 3, vals.get('amount') and vals.get('amount') or '', style)
#                 data_sheet.write(current_row, 4, vals.get('create_uid') and vals.get('create_uid') or '', style)
#                 # data_sheet.write(current_row, 8,
#                 #                  vals.get('pre_payment_reminding') and vals.get('pre_payment_reminding') or '0.00',
#                 #                  style)
#                 if not record.get('line'):
#
#                     current_row += 1
#
#                     continue
#                 i = 0
#                 # for line in record.get('line').itervalues():
#                 #
#                 #     if i > 0:
#                 #         data_sheet.write(current_row, 0,
#                 #                          vals.get('accounting_date') and vals.get('accounting_date') or '', style)
#                 #         data_sheet.write(current_row, 1, vals.get('department') and vals.get('department') or '', style)
#                 #     data_sheet.write(current_row, 2, line.get('expense_no') and line.get('expense_no') or '', style)
#                 #     data_sheet.write(current_row, 3, line.get('name') and line.get('name') or '', style)
#                 #     data_sheet.write(current_row, 4, line.get('amount') and line.get('amount') or '', style)
#                 #     current_row += 1
#                 #     i += 1
#
#             for x, i in enumerate([2, 2, 2, 2, 3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]):
#                 data_sheet.col(x).width = 2560 * i
#
#             for x in range(0, row):
#                 data_sheet.row(x).height_mismatch = 1
#                 data_sheet.row(x).height = 500
#
#             xls_wookbook.save(xls)
#             xls.seek(0)
#             content = xls.read()
#             return request.make_response(content, headers=[
#                 ('Content-Type', 'application/vnd.ms-excel'),
#                 ('Content-Disposition', 'attachment; filename=account_payment.xls;')
#             ])
#         else:
#             raise UserError(_('Error!'), _('These are no records no this period.'))

class ReturnPaymentReport(http.Controller):
    @http.route(['/report/linkloving_report.account_payment_income_report'], type='http', auth='user',
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
                u'到账日期', u'还款人', u'还款金额', u'客户', u'对账暂支单', u'人员'
            ]

            [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]

            current_row = 1
            for record in data.itervalues():
                vals = record.get('data')

                data_sheet.write(current_row, 0, vals.get('create_date') and vals.get('create_date') or '',
                                 style)
                data_sheet.write(current_row, 1, vals.get('employee_id') and vals.get('employee_id') or '', style)
                data_sheet.write(current_row, 2, vals.get('amount') and vals.get('amount') or '', style)
                data_sheet.write(current_row, 3, vals.get('payment_id') and vals.get('payment_id') or '', style)
                data_sheet.write(current_row, 4, vals.get('create_uid') and vals.get('create_uid') or '', style)
                # data_sheet.write(current_row, 8,
                #                  vals.get('pre_payment_reminding') and vals.get('pre_payment_reminding') or '0.00',
                #                  style)
                if not record.get('line'):
                    current_row += 1

                    continue
                i = 0
                # for line in record.get('line').itervalues():
                #
                #     if i > 0:
                #         data_sheet.write(current_row, 0,
                #                          vals.get('accounting_date') and vals.get('accounting_date') or '', style)
                #         data_sheet.write(current_row, 1, vals.get('department') and vals.get('department') or '', style)
                #     data_sheet.write(current_row, 2, line.get('expense_no') and line.get('expense_no') or '', style)
                #     data_sheet.write(current_row, 3, line.get('name') and line.get('name') or '', style)
                #     data_sheet.write(current_row, 4, line.get('amount') and line.get('amount') or '', style)
                #     current_row += 1
                #     i += 1

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
                ('Content-Disposition', 'attachment; filename=account_payment.xls;')
            ])
        else:
            raise UserError(_('Error!'), _('These are no records no this period.'))

            # class AccountPaymentReportIncmoing(http.Controller):
            #     @http.route(['/report/linkloving_report.account_payment_income_report'], type='http', auth='user',
            #                 multilang=True)
            #     def report_purchase(self, **data):
            #
            #         data = simplejson.loads(data['options'])
            #         if data:
            #             xls = StringIO.StringIO()
            #             xls_wookbook = xlwt.Workbook()
            #             data_sheet = xls_wookbook.add_sheet('data')
            #
            #             style = xlwt.easyxf(
            #                 'font: height 250;'
            #                 'alignment: vert center, horizontal center;'
            #                 'borders: left thin, right thin, top thin, bottom thin;'
            #             )
            #
            #             header_style = xlwt.easyxf(
            #                 'font: height 250, bold True;'
            #                 'borders: left thin, right thin, top thin, bottom thin;'
            #                 'align: vertical center, horizontal center;'
            #             )
            #
            #             header_list = [
            #                 u'支出日期', u'单号', u'供应商', u'金额', u'操作人'
            #             ]
            #
            #             [data_sheet.write(0, row, line, style) for row, line in enumerate(header_list)]
            #
            #             current_row = 1
            #             for record in data.itervalues():
            #                 vals = record.get('data')
            #
            #                 data_sheet.write(current_row, 0, vals.get('receive_date') and vals.get('receive_date') or '',
            #                                  style)
            #                 data_sheet.write(current_row, 1, vals.get('name') and vals.get('name') or '', style)
            #                 data_sheet.write(current_row, 2, vals.get('supplier') and vals.get('supplier') or '', style)
            #
            #                 data_sheet.write(current_row, 3, vals.get('amount') and vals.get('amount') or '', style)
            #                 data_sheet.write(current_row, 4, vals.get('create_uid') and vals.get('create_uid') or '', style)
            #                 # data_sheet.write(current_row, 8,
            #                 #                  vals.get('pre_payment_reminding') and vals.get('pre_payment_reminding') or '0.00',
            #                 #                  style)
            #                 if not record.get('line'):
            #
            #                     current_row += 1
            #
            #                     continue
            #                 i = 0
            #                 # for line in record.get('line').itervalues():
            #                 #
            #                 #     if i > 0:
            #                 #         data_sheet.write(current_row, 0,
            #                 #                          vals.get('accounting_date') and vals.get('accounting_date') or '', style)
            #                 #         data_sheet.write(current_row, 1, vals.get('department') and vals.get('department') or '', style)
            #                 #     data_sheet.write(current_row, 2, line.get('expense_no') and line.get('expense_no') or '', style)
            #                 #     data_sheet.write(current_row, 3, line.get('name') and line.get('name') or '', style)
            #                 #     data_sheet.write(current_row, 4, line.get('amount') and line.get('amount') or '', style)
            #                 #     current_row += 1
            #                 #     i += 1
            #
            #             for x, i in enumerate([2, 2, 2, 2, 3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]):
            #                 data_sheet.col(x).width = 2560 * i
            #
            #             for x in range(0, row):
            #                 data_sheet.row(x).height_mismatch = 1
            #                 data_sheet.row(x).height = 500
            #
            #             xls_wookbook.save(xls)
            #             xls.seek(0)
            #             content = xls.read()
            #             return request.make_response(content, headers=[
            #                 ('Content-Type', 'application/vnd.ms-excel'),
            #                 ('Content-Disposition', 'attachment; filename=account_payment.xls;')
            #             ])
            #         else:
            #             raise UserError(_('Error!'), _('These are no records no this period.'))
