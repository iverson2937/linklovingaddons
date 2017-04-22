# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingCore(http.Controller):
#     @http.route('/linkloving_core/linkloving_core/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_core/linkloving_core/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_core.listing', {
#             'root': '/linkloving_core/linkloving_core',
#             'objects': http.request.env['linkloving_core.linkloving_core'].search([]),
#         })

#     @http.route('/linkloving_core/linkloving_core/objects/<model("linkloving_core.linkloving_core"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_core.object', {
#             'object': obj
#         })