# -*- coding: utf-8 -*-
import base64
import json

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
        if active_type or my_load_file or active_id:
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
                'version': my_load_file_version,
            })
            args = {
                'filename': my_load_file.filename,
                'mimetype': my_load_file.content_type,
                'id': attach.id
            }
        except Exception:
            error = {'error': _("Something horrible happened")}
            _logger.exception("Fail to upload attachment %s" % my_load_file.filename)
        return out % (func, json.dumps(args), json.dumps({"error": error}))

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

    @http.route('/update_attachment_info', type='json', auth='none')
    def update_attachment_info(self):
        attachment_id = request.jsonrequest.get("attachment_id")  # 附件id
        path = request.jsonrequest.get("path")  # 远程地址

        return json.dumps({
            "msg": u"得到的参数",
            "attachment_id": attachment_id,
            "path": path,
        })
