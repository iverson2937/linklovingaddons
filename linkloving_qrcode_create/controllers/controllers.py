# -*- coding: utf-8 -*-
import base64
import json

from odoo import http

# class LinklovingQrcodeCreate(http.Controller):
#     @http.route('/linkloving_qrcode_create/linkloving_qrcode_create/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_qrcode_create/linkloving_qrcode_create/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_qrcode_create.listing', {
#             'root': '/linkloving_qrcode_create/linkloving_qrcode_create',
#             'objects': http.request.env['linkloving_qrcode_create.linkloving_qrcode_create'].search([]),
#         })

#     @http.route('/linkloving_qrcode_create/linkloving_qrcode_create/objects/<model("linkloving_qrcode_create.linkloving_qrcode_create"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_qrcode_create.object', {
#             'object': obj
#         })
from odoo.http import request, content_disposition


class Binary(http.Controller):
    @http.route('/web/binary/download_qrcode', type='http', auth="public", csrf=False)
    def download_qrcode(self,model,field,id,filename=None, **kw):
        Model = request.env[model]
        product_obj = Model.sudo().search([('id', '=', id)], limit=1)[0]
        img_str = product_obj.action_qrcode_download()
        filecontent = base64.b64decode(img_str)
        if not filecontent:
            return request.not_found()
        else:
            return request.make_response(filecontent,
                                     [('Content-Type', 'image/png'),
                                      ('Content-Disposition', content_disposition(filename))])


    @http.route('/web/binary/download_multi_qrcode', type='http', auth="public", csrf=False)
    def download_multi_qrcode(self,model,field,ids,filename=None, **kw):
        idss = json.loads(ids)
        Model = request.env[model]
        product_objs = Model.sudo().search([('id', 'in', idss)])
        content = product_objs.multi_create_qrcode()
        filecontent = content.getvalue()
        if not filecontent:
            return request.not_found()
        else:
            return request.make_response(filecontent,
                                     [('Content-Type', 'application/octet-stream'),
                                      ('Content-Disposition', content_disposition(filename))])


