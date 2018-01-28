# coding=utf-8
import calendar
import json
import logging
import os

import StringIO

import operator
import urllib
import urllib2
from datetime import datetime, timedelta, date
from itertools import groupby
from operator import attrgetter
from odoo.http import content_disposition, dispatch_rpc, request, Controller, route
import collections
from xlwt import *

from odoo import tools
from ..utils.excel_tools import MyWorkbook



_logger = logging.getLogger(__name__)

# 设置报表内字体样式

title_font = Font()
title_font.name = 'Times New Roman'
title_font.bold = True
title_font.height = 400

head_font = Font()
head_font.name = 'Times New Roman'
head_font.height = 220

bold_font = Font()
bold_font.bold = True
bold_font.height = 230

alignment = Alignment()
alignment.horz = Alignment.HORZ_CENTER
alignment.vert = Alignment.VERT_CENTER
alignment.wrap = Alignment.WRAP_AT_RIGHT

borders = Borders()
borders.left = 1
borders.right = 1
borders.top = 1
borders.bottom = 1
borders.bottom_colour = 0x3A

common_style = XFStyle()
common_style.alignment = alignment
common_style.borders = borders

bold_style = XFStyle()
bold_style.font = bold_font
bold_style.alignment = alignment

datetime_style = XFStyle()
datetime_style.num_format_str = 'YYYY-MM-DD'
datetime_style.alignment = alignment
datetime_style.borders = borders

title_style = XFStyle()
title_style.font = title_font
title_style.alignment = alignment

head_style = XFStyle()
head_style.font = head_font
head_style.alignment = alignment
head_style.borders = borders


def content_disposition(filename):
    filename = ustr(filename)
    escaped = urllib2.quote(filename.encode('utf8'))
    browser = request.httprequest.user_agent.browser
    version = int((request.httprequest.user_agent.version or '0').split('.')[0])
    if browser == 'msie' and version < 9:
        return "attachment; filename=%s" % escaped
    elif browser == 'safari' and version < 537:
        return u"attachment; filename=%s" % filename.encode('ascii', 'replace')
    else:
        return "attachment; filename*=UTF-8''%s" % escaped

def check_file(filename, num=1):
    exist_file = os.path.exists(filename)
    if exist_file:
        name, suffix = filename.split('.')
        if ' ' in name:
            pre, suf = name.split(' ')
            name = pre
        filename = name + ' (%r)' % num + '.' + suffix
        num += 1
        return check_file(filename.decode('utf-8'), num=num)
    else:
        return filename

def write_title(xls, xlstitle, col):
    """
    写入excel标题
    :param xls: Workbook实例
    :param title: excel标题
    :param col: 表的总列数
    :return:
    """
    xls.write_merge(0, 0, 0, col, xlstitle, title_style)

def write_header(xls, xlsheader):
    """
    写入excel表头
    :param xls: Workbook实例
    :param xlsheader: excel表头及其位置的列表
    :return:
    """
    for a_header in xlsheader:
        name, col = a_header.split(' ')
        try:
            col1, col2 = col.split(',')
        except ValueError:
            try:
                xls.write_merge(1, 2, int(col), int(col), name, head_style)
            except Exception:
                xls.write(2, int(col), name, head_style)
        else:
            xls.write_merge(1, 1, int(col1), int(col2), name, head_style)

def check_if_last_id(xls, current_id, filter_ids, excel_row, col, part_name, part_price, total_name, total_price):
    if current_id == filter_ids[-1]:
        xls.write(excel_row, col, part_name, bold_style)
        xls.write(excel_row, col + 1, part_price, bold_style)
        xls.write(excel_row + 1, col, total_name, bold_style)
        xls.write(excel_row + 1, col + 1, total_price, bold_style)


def set_cols_width(xls, size, cols):
    size = int(size)
    for col in cols:
        xls.col(col).width = 256 * size





def task_plan_export(values):
    values = urllib.unquote(values)
    values = json.loads(values)
    task_table = request.registry.get('ljwj.sale.order.line.install')
    tasks = task_table.browse(request.cr, request.uid, values)
    # tasks_by_order_num = groupby(tasks, attrgetter('sale_order_id'))
    wb = MyWorkbook(encoding='utf-8')
    sheet_title = u"任务计划表"
    ws = wb.add_sheet(sheet_title)
    head = [u"序号", u"地址", u"城市", u"甲方", u"项目编号", u"业主", u"业主联系方式", u"现场负责人", u"负责人联系方式",
            u"产品类别", u"服务类别", u"商家合同号", u"负责工头", u"负责工匠", u"工匠预约日期", u"实际上门日期", u"下单备注", u"延期备注"]
    ws.write_merge(0, 0, 0, 17, sheet_title, title_style)
    wb.multiple_append(head, style=head_style)
    for index, task in enumerate(tasks):
        index += 1
        content = [index]
        task_base = get_task_base(task)
        for a_item in [u"地址", u"城市", u"甲方", u"项目编号", u"业主", u"业主联系方式", u"现场负责人", u"负责人联系方式",
            u"产品类别", u"服务类别", u"商家产品编号", u"负责工头", u"负责工匠", u"工匠预约日期", u"实际上门日期", u"下单备注", u"延期备注"]:
            item = task_base.get(a_item, '')
            content.append(item)
        wb.multiple_append(content, style=common_style)
    filename = u'任务计划表.xls'
    sio = StringIO.StringIO()
    wb.save(sio)
    sio.seek(0)
    data = sio.read()
    sio.close()
    return filename, data




class ExportReport(Controller):

    @route('/export/task_plan', type='http', auth='public', csrf=False)
    def task_plan(self, values):
        filename, data = task_plan_export(values)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])

    @route('/export/exception_feedback', type='http', auth='public', csrf=False)
    def exception_feedback(self, values):
        filename, data = exception_feedback_export(values)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])

    @route('/export/task_statistic', type='http', auth='public', csrf=False)
    def task_statistic(self, values):
        user = request.env.user
        if request.env.ref('ljwj_core.group_customer') in user.groups_id:
            filename, data = task_statistic_export_partyA(values)
        elif request.env.ref('ljwj_core.group_ljwj_worker') in user.groups_id:
            filename, data = task_statistic_export_worker(values)
        else:
            filename, data = task_statistic_export(values)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])

    @route('/export/attendance_xls', type='http', auth='public', csrf=False)
    def worker_attendance(self, values, order):
        filename, data = worker_attendance_export(values, order)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])

    @route('/export/order_total', type='http', auth='public', csrf=False)
    def order_total(self, values, order):
        filename, data = order_total_export(values, order)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])

    @route('/export/worker_unstatement', type='http', auth='public', csrf=False)
    def unstatement_total(self, values, worker):
        filename, data = worker_unstatement_export(values, worker)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])

    @route('/export/partyA_bill', type='http', auth='public', csrf=False)
    def partyA_bill(self, values):
        filename, data = partyA_bill_xls_export(values)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])

    @route('/export/sale_order_base_info_template', type='http', auth='public', csrf=False)
    def sale_order_base_info_template(self):
        path = config.downexcel() + os.path.sep + u'基础信息导入模板.xlsx'
        if not os.path.exists(path):
            _logger.error('未读取到模板')
            return
        else:
            data = open(path, 'rb')
        filename = u'基础信息导入模板.xlsx'
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])

    @route('/export/sale_order_quotation_template', type='http', auth='public', csrf=False)
    def sale_order_quotation_template(self):
        path = config.downexcel() + os.path.sep + u'报价导入模板.xlsx'
        if not os.path.exists(path):
            _logger.error('未读取到模板')
            return
        else:
            data = open(path, 'rb')
        filename = u'报价导入模板.xlsx'
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])