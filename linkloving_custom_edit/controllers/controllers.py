# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingCustomEdit(http.Controller):
#     @http.route('/linkloving_custom_edit/linkloving_custom_edit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_custom_edit/linkloving_custom_edit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_custom_edit.listing', {
#             'root': '/linkloving_custom_edit/linkloving_custom_edit',
#             'objects': http.request.env['linkloving_custom_edit.linkloving_custom_edit'].search([]),
#         })

#     @http.route('/linkloving_custom_edit/linkloving_custom_edit/objects/<model("linkloving_custom_edit.linkloving_custom_edit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_custom_edit.object', {
#             'object': obj
#         })
