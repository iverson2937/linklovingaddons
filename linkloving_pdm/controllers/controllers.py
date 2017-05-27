# -*- coding: utf-8 -*-
import base64
import json

from odoo import http, _
from odoo.http import serialize_exception, request, _logger


class LinklovingPdm(http.Controller):
    @http.route('/linkloving_pdm/upload_attachment_info', type='http', auth='user')
    def index(self, active_id, active_type, my_load_file_name, my_load_file, my_load_file_remote_path,
              my_load_file_version, **kwargs):
        Model = request.env['product.attachment.info']
        out = """<script language="javascript" type="text/javascript">
                    var win = window.top.window;
                    win.jQuery(win).trigger(%s, %s);
                </script>"""
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
            args = {'error': _("Something horrible happened")}
            _logger.exception("Fail to upload attachment %s" % my_load_file.filename)
        return out % (json.dumps(None), json.dumps(args))

    @http.route('/linkloving_pdm/update_attachment_info', type='http', auth='user')
    def update_attachment_info(self, **kw):
        return True
