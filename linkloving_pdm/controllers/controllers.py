# -*- coding: utf-8 -*-
import base64
import json

import werkzeug

from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import serialize_exception, request, _logger


class LinklovingPdm(http.Controller):
    @http.route('/linkloving_pdm/upload_attachment_info', type='http', auth='user')
    def index(self, func, active_id, active_type, my_load_file_name, my_load_file, my_load_file_remote_path,
              my_load_file_version, **kwargs):
        Model = request.env['product.attachment.info']
        out = """<script type='text/javascript'>
            window.parent['%s'](%s, %s);
        </script>"""
        if not active_type or not (my_load_file or my_load_file_remote_path) or not active_id:
            error = u"缺少必要的参数"
            args = {"error": error}
            return out % (func, json.dumps(args), json.dumps({}))
        try:
            attach = Model.create({
                'file_name': my_load_file_name,
                'file_binary': base64.encodestring(my_load_file.read()),
                'remote_path': my_load_file_remote_path,
                'state': 'waiting_release',
                'product_tmpl_id': int(active_id),
                'type': active_type,
                'version': Model.with_context({"product_id": int(active_id),
                                               "type": active_type})._default_version(),
            })
            filename = attach.get_download_filename()
            attach.file_name = filename
            args = {
                'filename': filename,
                'mimetype': my_load_file.content_type,
                'id': attach.id
            }
        except Exception:
            error = {'error': _("Something horrible happened")}
            _logger.exception("Fail to upload attachment %s" % my_load_file.filename)
        return out % (func, json.dumps(args), json.dumps({}))

    # @http.route('/linkloving_pdm/update_attachment_info', type='http', auth='user')
    # def update_attachment_info(self, attachment_id, new_file):
    #     attachment = request.env['product.attachment.info'].browse(attachment_id)
    #     out = """<script language="javascript" type="text/javascript">
    #                 var win = window.top.window;
    #                 win.jQuery(win).trigger(%s, %s);
    #             </script>"""
    #
    #     attach = attachment.write({
    #         'file_name': new_file.filename,
    #     })
    #
    #     return json.dumps({"error": "123"})
    #

    @http.route('/update_attachment_info', type='http', auth='none')
    def update_attachment_info(self, attachment_id=None, file=None, result=None):
        # attachment_id = request..get("attachment_id")  # 附件id
        # file = request.jsonrequest.get("file")  # 远程地址
        # result = request.jsonrequest.get("result")
        print result
        return json.dumps({
            "msg": u"得到的参数",
            "attachment_id": attachment_id,
            "file": file,
            "result": result,
        })

    @http.route('/download_file', type='http', auth='none')
    def content_common(self, xmlid=None, model='product.attachment.info', id=None, field='file_binary', filename=None,
                       filename_field='datas_fname', unique=None, mimetype=None, download=None, data=None, token=None):
        if not filename:
            info = request.env[model].sudo().browse(int(id))
            filename = info.get_download_filename()
        status, headers, content = request.registry['ir.http'].binary_content(xmlid=xmlid, model=model, id=id,
                                                                              field=field, unique=unique,
                                                                              filename=filename,
                                                                              filename_field=filename_field,
                                                                              download=download, mimetype=mimetype)
        if status == 304:
            response = werkzeug.wrappers.Response(status=status, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200:
            response = request.not_found()
        else:
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)
        if token:
            response.set_cookie('fileToken', token)
        return response
