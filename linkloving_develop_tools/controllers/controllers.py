# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingDevelopTools(http.Controller):
#     @http.route('/linkloving_develop_tools/linkloving_develop_tools/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_develop_tools/linkloving_develop_tools/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_develop_tools.listing', {
#             'root': '/linkloving_develop_tools/linkloving_develop_tools',
#             'objects': http.request.env['linkloving_develop_tools.linkloving_develop_tools'].search([]),
#         })

#     @http.route('/linkloving_develop_tools/linkloving_develop_tools/objects/<model("linkloving_develop_tools.linkloving_develop_tools"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_develop_tools.object', {
#             'object': obj
#         })
