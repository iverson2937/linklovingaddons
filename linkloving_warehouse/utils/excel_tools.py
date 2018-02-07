# -*- coding:utf-8 -*-
from xlwt import *


class MyWorkbook(Workbook):
    num = 0

    def count_row_col(self, values):
        MyWorkbook.num += 1
        shallow_extra = 0
        deep_extra = 0
        for content in values:
            if isinstance(content, list):
                temp_s_extra = len(content) - 1
                if shallow_extra < temp_s_extra:
                    shallow_extra = temp_s_extra
                temp_d_extra = 0
                for s_content in content:
                    if isinstance(s_content, list):
                        temp_d_extra += self.count_row_col(s_content)
                        if deep_extra < temp_d_extra:
                            deep_extra = temp_d_extra
                        else:
                            continue
        total_extra = shallow_extra + deep_extra

        return total_extra

    def multiple_cells(self, values, sheet, start_col=0, start_row=0, horizontal=True, style=None, indent=0):
        extra = self.count_row_col(values)
        inner_extra = None
        for index, content in enumerate(values):
            # print ' ' * indent, '*' * 20
            # print ' ' * indent, 'index, content', index, content
            if inner_extra:
                # print extra, inner_extra
                index += inner_extra
            if not horizontal:
                current_col, current_row = start_col, start_row + index
                last_col, last_row = start_col + extra, current_row
                # print ' ' * indent, 'horizontal', horizontal
                # print ' ' * indent, 'current_col ', current_col, ', current_row ', current_row, '= ', 'start_col ', start_col, ', start_row ', start_row, '+ index ', index
                # print ' ' * indent, 'last_col ', last_col, ', last_row ', last_row, '= ', 'start_col ', start_col, '+ extra ', extra, ', current_row ', current_row
            else:
                current_col, current_row = start_col + index, start_row
                last_col, last_row = current_col, start_row + extra
                # print ' ' * indent, 'horizontal', horizontal
                # print ' ' * indent, 'current_col ', current_col, ', current_row ', current_row, '= ', 'start_col ', start_col, '+ index ', index, ', start_row ', start_row
                # print ' ' * indent, 'last_col ', last_col, ', last_row ', last_row, '= ', 'current_col ', current_col, ', start_row ', start_row, '+ extra ', extra
            if isinstance(content, list):
                next_horizontal = False if horizontal else True
                # print ' ' * indent, 'before entra next', current_col, current_row
                last_extra = self.multiple_cells(content, sheet, start_col=current_col, start_row=current_row,
                                                 horizontal=next_horizontal, style=style, indent=indent + 4)
                # print 'last_extra', last_extra, 'inner_extra',inner_extra
                last_extra += inner_extra if inner_extra else 0
                if inner_extra < last_extra:
                    inner_extra = last_extra
            else:
                # print ' ' * indent, 'write merge cell', current_col, current_row, last_col, last_row, content
                # print ' ' * indent, '%' * 20
                if not style:
                    sheet.write_merge(current_row, last_row, current_col, last_col, content)
                else:

                    sheet.write_merge(current_row, last_row, current_col, last_col, content, style)
                if sheet.last_used_row < last_row:
                    sheet.last_used_row = last_row
                # print 'current', sheet.last_used_row
        return extra

    def multiple_append(self, iterable, sheet=None, col=0, horizontal=True, style=None):
        if not sheet:
            sheet = self.get_active_sheet()
            try:
                sheet = self.get_sheet(sheet)
            except IndexError:
                sheet = self.add_sheet('Sheet')
        assert isinstance(sheet, Worksheet), 'sheet must be a instance of Worksheet!'
        row_idx = sheet.last_used_row + 1
        # print 'last', sheet.last_used_row
        if isinstance(iterable, list):
            self.multiple_cells(iterable, sheet=sheet, start_col=col, start_row=row_idx, horizontal=horizontal,
                                style=style)
        else:
            raise ValueError('values must be a list!')


def worker_xls_export():
    wb = MyWorkbook(encoding='utf-8')
    ws = wb.add_sheet(u'hahaha')
    # wb.multiple_append(
    #     [
    #         '0,1,0,4',
    #         '1,1,1,4',
    #         [
    #             ['2,1,2,2','3,1,3,2',[['4,1,4,1','5,1,5,1'], ['4,2,4,2','5,2,5,2']],'6,1,6,2','7,1,7,2'],
    #             ['2,3,2,3','3,3,3,3',[['4,3,4,3','5,3,5,3']],'6,3,6,3','7,3,7,3'],
    #             ['2,4,2,4','3,4,3,4',[['4,4,4,4','5,4,5,4']],'6,4,6,4','7,4,7,4'],
    #             ['2,1,2,2', '3,1,3,2', [['4,1,4,1', '5,1,5,1'], ['4,2,4,2', '5,2,5,2']], '6,1,6,2', '7,1,7,2']
    #         ],
    #         '8,1,8,4',
    #         '9,1,9,4'
    #     ])
    # wb.multiple_append(
    #     [
    #         '0,1,0,4',
    #         '1,1,1,4',
    #         [
    #             ['2,1,2,2','3,1,3,2',[['4,1,4,1','5,1,5,1']],'6,1,6,2','7,1,7,2'],
    #         ],
    #         '8,1,8,4',
    #         '9,1,9,4'
    #     ])
    # wb.multiple_append(
    #     [
    #         '0,1,0,4',
    #         '1,1,1,4',
    #         [
    #             ['2,1,2,2','3,1,3,2',[['4,1,4,1','5,1,5,1'], ['4,2,4,2','5,2,5,2']],'6,1,6,2','7,1,7,2'],
    #         ],
    #         '8,1,8,4',
    #         '9,1,9,4'
    #     ])
    wb.multiple_append(
        [
            '0,1,0,4',
            '1,1,1,4',
            [
                ['2,1,2,2', '3,1,3,2', [['4,1,4,1', '5,1,5,1'], ['4,2,4,2', '5,2,5,2']], '6,1,6,2', '7,1,7,2'],
                ['2,1,2,2', '3,1,3,2', [['4,1,4,1', '5,1,5,1'], ['4,2,4,2', '5,2,5,2']], '6,1,6,2', '7,1,7,2'],
                ['2,1,2,2', '3,1,3,2', [['4,1,4,1', '5,1,5,1']], '6,1,6,2', '7,1,7,2'],
                # ['2,1,2,2', '3,1,3,2', [['4,1,4,1', '5,1,5,1']], '6,1,6,2', '7,1,7,2'],
                # ['2,1,2,2', '3,1,3,2', [['4,1,4,1', '5,1,5,1'], ['4,2,4,2', '5,2,5,2']], '6,1,6,2', '7,1,7,2'],
            ],
            '8,1,8,4',
            '9,1,9,4'
        ])
    wb.multiple_append(
        [
            '0,1,0,4',
            '1,1,1,4',
            [
                ['2,1,2,2', '3,1,3,2', [['4,1,4,1', '5,1,5,1']], '6,1,6,2', '7,1,7,2'],
            ],
            '8,1,8,4',
            '9,1,9,4'
        ])

    # wb.multiple_append(
    # [
    #     '0,1,0,4',
    #     '1,1,1,4',
    #     [
    #
    #         ['2,4,2,4', '3,4,3,4', [['4,4,4,4', '5,4,5,4']], '6,4,6,4', '7,4,7,4']
    #     ],
    #     '8,1,8,4',
    #     '9,1,9,4',
    #     [
    #         ['10,1,10,1', '11,1,11,1'],
    #         ['10,2,10,2', '11,2,11,2']
    #
    #     ],
    #     '12,1,12,4',
    #     '13,1,13,4'
    # ])
    # wb.multiple_append(
    #     [88, u'\u6709\u4f4f(\u767e\u53d8\u52a0)', u'\u6b66\u6c49\u5e02', u'\u6d4b\u8bd52\u53d6\u4e00\u5f85',
    #      u'\u6d4b\u8bd5\u4e1a\u4e3b\u5148\u770b\u770b\u7684\u5730\u5740\u554a', [
    #          [u'\u6a71\u67dc', '\xe5\xae\x89\xe8\xa3\x85 \xe4\xb8\xbb\xe4\xbb\xbb\xe5\x8a\xa1',
    #           [[u'\u666e\u901a\u6a71\u67dc\u7c7b', u'\u5ef6\u7c73', 1.0, 160.0],
    #            [u'\u7682\u6db2\u5668', u'\u4e2a', 2.0, 10.0]], 180.0, 0, 180.0, '',
    #           '\xe7\xbb\x93\xe7\xae\x97\xe5\xae\x8c\xe6\x88\x90'],
    #          [u'\u6210\u54c1\u53f0\u9762', '\xe5\xae\x89\xe8\xa3\x85 \xe4\xb8\xbb\xe4\xbb\xbb\xe5\x8a\xa1',
    #           [[u'\u53f0\u9762(\u4e01\u9999\u767d)', u'\u7c73', 2.0, 396.0]], 0, 0, 792.0, '',
    #           '\xe4\xbb\xbb\xe5\x8a\xa1\xe5\x8f\x96\xe6\xb6\x88'],
    #          [u'\u5bb6\u5177', '\xe5\xae\x89\xe8\xa3\x85 \xe4\xb8\xbb\xe4\xbb\xbb\xe5\x8a\xa1',
    #           [[u'\u8863\u67dc\uff08\u63a8\u62c9\u95e8\uff09', u'\u5e73\u7c73', 3.0, 150.0],
    #            [u'\u6d88\u6bd2\u67dc', u'\u53f0', 1.0, 29.7]], 0, 0, 479.7, '',
    #           '\xe4\xbb\xbb\xe5\x8a\xa1\xe5\x8f\x96\xe6\xb6\x88'],
    #          [u'\u6a71\u67dc', '\xe7\x9f\xad\xe9\xa9\xb3 \xe4\xb8\xbb\xe4\xbb\xbb\xe5\x8a\xa1', [['', '', '', '']],
    #           400.0, 0, 400.0, '', '\xe7\xbb\x93\xe7\xae\x97\xe5\xae\x8c\xe6\x88\x90']], 580.0, u'L-BBJ-20170217-0003',
    #      '2017-02-17']
    # )
    filename = u'test.xls'
    wb.save(filename)


if __name__ == '__main__':
    worker_xls_export()
