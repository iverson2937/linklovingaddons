# -*- coding: utf-8 -*-
import StringIO

import xlwt

from odoo import http
from odoo.http import request, content_disposition


class LinklovingNewBomUpdate(http.Controller):
    @http.route('/linkloving_new_bom_update/linkloving_new_bom_update/', type='http', auth="public", csrf=False)
    def index(self, model, id_list, file_type):

        bom_list = id_list.replace('[', '').replace(']', '').split(',')
        if file_type == 'bom_structure':
            # 结构
            content = self.write_structure_excel(model, bom_list)
            filename = 'Bom 结构'
        else:
            # 成本
            content = self.write_costing_excel(model, bom_list)
            filename = 'Bom 成本'

        return request.make_response(content, headers=[
            ('Content-Type', 'application/vnd.ms-excel'),
            ('Content-Disposition', content_disposition(filename + '.xlsx'))
        ])

    def set_style(self, name, height, bold=False):
        style = xlwt.XFStyle()  # 初始化样式

        font = xlwt.Font()  # 为样式创建字体
        font.name = name  # 'Times New Roman'
        font.bold = bold
        font.color_index = 4
        font.height = height

        # borders = xlwt.Borders()
        # borders.left = 6
        # borders.right = 6
        # borders.top = 6
        # borders.bottom = 6

        style.font = font
        # style.borders = borders

        return style

    #  Bom 成本
    def write_costing_excel(self, model, bom_list):

        f = xlwt.Workbook()  # 创建工作簿

        xls = StringIO.StringIO()

        style = xlwt.easyxf(
            'font: height 250;'
            'alignment: vert center, horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
        )

        '''
        创建第一个sheet:
          sheet1
        '''

        bom_id = 0
        for bom_one_id in bom_list:
            bom_id += 1
            mrp_bom_data = request.env[model].sudo().search([('id', '=', int(bom_one_id))])

            sheet1 = f.add_sheet(u'sheet' + str(bom_id), cell_overwrite_ok=True)  # 创建sheet

            for ss in range(0, len(mrp_bom_data.bom_line_ids)):
                first_col = sheet1.col(ss)
                first_col.width = 300 * 70 if ss == 0 else 300 * 40

            row0 = [u'原材料', u'数量', u'单位成本', u'总成本']

            sheet1.write_merge(0, 0, 0, 3, mrp_bom_data.display_name, self.set_style('Arial', 300, True))  # 第一列

            sheet1.write_merge(2, 2, 0, 2, str(mrp_bom_data['product_qty']) + mrp_bom_data.product_uom_id['name'],
                               self.set_style('Arial', 220))
            #
            sheet1.write_merge(4, 5, 0, 3, u'成本结构', self.set_style('Arial', 220, True))

            # 生成第一行
            for i in range(0, len(row0)):
                sheet1.write(6, i, row0[i], style)
            j = 6
            for data in mrp_bom_data.bom_line_ids:
                j += 1
                sheet1.write(j, 0, data['display_name'], style)
                sheet1.write(j, 1, str(data['product_qty']) + data.product_uom_id['name'], style)
                sheet1.write(j, 2, data.product_id['standard_price'], style)
                sheet1.write(j, 3, data['product_qty'] * data.product_id['standard_price'], style)

        # f.save('demo1.xlsx')  # 保存文件

        f.save(xls)
        xls.seek(0)

        content = xls.read()
        return content

    # 写excel  结构
    def write_structure_excel(self, model, bom_list):

        f = xlwt.Workbook()  # 创建工作簿

        xls = StringIO.StringIO()

        style = xlwt.easyxf(
            'font: height 250;'
            'align: wrap on;'
            'alignment: vert center, horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
        )

        '''
        创建第一个sheet:
          sheet1
        '''
        bom_id = 0
        for bom_one_id in bom_list:
            bom_id += 1
            mrp_bom_data = request.env[model].sudo().search([('id', '=', int(bom_one_id))])

            sheet1 = f.add_sheet(u'sheet' + str(bom_id), cell_overwrite_ok=True)  # 创建sheet

            tall_style = xlwt.easyxf('font:height 800;')  # 36pt,类型小初的字号

            for bom_data_int in range(0, len(mrp_bom_data.bom_line_ids)):
                first_col = sheet1.col(bom_data_int)
                first_col.width = 250 * 40

            for bom_data_int in range(0, len(mrp_bom_data.bom_line_ids) + 1):
                first_row = sheet1.row(bom_data_int)
                first_row.set_style(tall_style)

            row0 = [u'序号', u'Bom 名称', u'Bom 规格', u'数量', u'Bom 参考']

            sheet1.write_merge(0, 0, 0, 3, u'Bom 结构', self.set_style('Arial', 300, True))  # 第一列

            # 生成第一行
            for i in range(0, len(row0)):
                sheet1.write(1, i, row0[i], style)

            jj = 1
            for mrp_bom_one in mrp_bom_data:
                jj += 1
                sheet1.write(jj, 0, jj - 1, style)
                sheet1.write(jj, 1, mrp_bom_one.display_name, style)
                sheet1.write(jj, 2, mrp_bom_one.product_specs, style)
                sheet1.write(jj, 3, str(mrp_bom_one['product_qty']) + mrp_bom_one.product_uom_id['name'], style)
                sheet1.write(jj, 4, mrp_bom_one['code'], style)
            j = 2
            for data in mrp_bom_data.bom_line_ids:
                j += 1
                sheet1.write(j, 0, j - 2, style)
                sheet1.write(j, 1, data.display_name, style)
                sheet1.write(j, 2, data.product_id['product_specs'], style)
                sheet1.write(j, 3, str(data['product_qty'] * data.product_id['standard_price']), style)
                sheet1.write(j, 4, [adc.display_name for adc in data.child_line_ids], style)

        f.save(xls)
        xls.seek(0)
        content = xls.read()
        return content
