# -*- coding: utf-8 -*-
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