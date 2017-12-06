# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingCustomAuth(http.Controller):
#     @http.route('/linkloving_custom_auth/linkloving_custom_auth/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_custom_auth/linkloving_custom_auth/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_custom_auth.listing', {
#             'root': '/linkloving_custom_auth/linkloving_custom_auth',
#             'objects': http.request.env['linkloving_custom_auth.linkloving_custom_auth'].search([]),
#         })

#     @http.route('/linkloving_custom_auth/linkloving_custom_auth/objects/<model("linkloving_custom_auth.linkloving_custom_auth"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_custom_auth.object', {
#             'object': obj
#         })