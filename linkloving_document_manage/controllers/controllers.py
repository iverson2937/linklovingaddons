# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingDocumentManage(http.Controller):
#     @http.route('/linkloving_document_manage/linkloving_document_manage/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_document_manage/linkloving_document_manage/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_document_manage.listing', {
#             'root': '/linkloving_document_manage/linkloving_document_manage',
#             'objects': http.request.env['linkloving_document_manage.linkloving_document_manage'].search([]),
#         })

#     @http.route('/linkloving_document_manage/linkloving_document_manage/objects/<model("linkloving_document_manage.linkloving_document_manage"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_document_manage.object', {
#             'object': obj
#         })