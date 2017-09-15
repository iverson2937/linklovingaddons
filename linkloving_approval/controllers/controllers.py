# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class LinklovingApproval(http.Controller):
    @http.route('/selectfile/file_show', type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def order_status_show(self, **kw):
        file_id = kw.get('id')
        attachment_info = request.env['product.attachment.info'].browse(int(file_id))
        version_data_list = request.env['product.attachment.info'].search(
            [('product_tmpl_id', '=', attachment_info.product_tmpl_id.id)])
        attach_list = []
        for atta in version_data_list:
            attach_list.append(atta.convert_attachment_info())
        for attach_one in attach_list:
            for review_line_one in attach_one.get('review_line'):
                review_line_one['title'] = '备注:' + str(review_line_one.get('remark')) + ',审核结果：' + str(
                    review_line_one.get('state')[1]) + '，时间：' + str(review_line_one.get('create_date'))
        values = {
            'attach_list': attach_list,
        }
        return request.render("linkloving_approval.file_show", values)
