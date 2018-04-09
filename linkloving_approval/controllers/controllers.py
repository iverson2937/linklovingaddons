# -*- coding: utf-8 -*-
import base64
import cStringIO
import zipfile
import os, zipfile

import qrcode

from odoo import http
from odoo.http import request

import sys
from odoo.http import request, content_disposition

reload(sys)
sys.setdefaultencoding("utf-8")


class LinklovingApproval(http.Controller):
    @http.route('/selectfile/file_show', type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def order_status_show(self, **kw):
        file_id = kw.get('id')
        file_type = kw.get('type')
        if file_type == '工程':
            file_type = 'project'
        else:
            file_type = file_type.lower()
        ATTACHINFO_FIELD = ['product_tmpl_id', 'file_name', 'review_id', 'remote_path',
                            'version', 'state', 'has_right_to_review', 'is_show_outage',
                            'is_able_to_use', 'is_show_cancel', 'is_first_review',
                            'create_uid', 'type', 'is_delect_view', 'is_show_action_deny']

        attachment_info = request.env['product.attachment.info'].browse(int(file_id))
        version_data_list = request.env['product.attachment.info'].search_read(
            [('product_tmpl_id', '=', attachment_info.product_tmpl_id.id), ('type', '=', file_type)],
            fields=ATTACHINFO_FIELD)
        attach_list = []
        for atta in version_data_list:
            list_atta = request.env['product.attachment.info'].sudo().convert_attachment_info(atta)
            temp_review_line = list_atta['review_line']
            temp_review_line.reverse()
            list_atta['review_line'] = temp_review_line

            attach_list.append(list_atta)

        for attach_one in attach_list:
            for review_line_one in attach_one.get('review_line'):
                review_line_one['title'] = '备注:' + str(review_line_one.get('remark')) + ',审核结果：' + str(
                    review_line_one.get('state')[1] if review_line_one.get('state') != ' ' else ' ') + '，时间：' + str(
                    review_line_one.get('create_date'))
        values = {
            'attach_list': attach_list,
        }
        return request.render("linkloving_approval.file_show", values)

    @http.route('/linkloving_approval/linkloving_approval/', type='http', auth="public", csrf=False)
    def indexss(self):
        return "ping"

    @http.route('/linkloving_approval/all_download_file', type='http', auth='none')
    def index_download(self, xmlid=None, model='product.attachment.info', field='file_binary', filename=None,
                       filename_field='datas_fname', unique=None, mimetype=None, download=None, data=None, token=None,
                       file_list=None):

        zip_buffer = cStringIO.StringIO()
        f = zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED)

        for file_id in file_list.split(','):
            info = request.env[model].sudo().browse(int(file_id))

            status, headers, content = request.registry['ir.http'].binary_content(xmlid=xmlid, model=model,
                                                                                  id=int(file_id),
                                                                                  field=field, unique=unique,
                                                                                  filename=filename,
                                                                                  filename_field=filename_field,
                                                                                  download=download, mimetype=mimetype)
            f.writestr(info.file_name, base64.b64decode(content))

        f.close()

        return request.make_response(zip_buffer.getvalue(),
                                     [('Content-Type', 'application/octet-stream'),
                                      ('Content-Disposition', content_disposition(filename))])
