# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAuthGroup(http.Controller):
#     @http.route('/linkloving_auth_group/linkloving_auth_group/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_auth_group/linkloving_auth_group/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_auth_group.listing', {
#             'root': '/linkloving_auth_group/linkloving_auth_group',
#             'objects': http.request.env['linkloving_auth_group.linkloving_auth_group'].search([]),
#         })

#     @http.route('/linkloving_auth_group/linkloving_auth_group/objects/<model("linkloving_auth_group.linkloving_auth_group"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_auth_group.object', {
#             'object': obj
#         })
