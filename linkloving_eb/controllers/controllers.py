# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingEb(http.Controller):
#     @http.route('/linkloving_eb/linkloving_eb/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_eb/linkloving_eb/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_eb.listing', {
#             'root': '/linkloving_eb/linkloving_eb',
#             'objects': http.request.env['linkloving_eb.linkloving_eb'].search([]),
#         })

#     @http.route('/linkloving_eb/linkloving_eb/objects/<model("linkloving_eb.linkloving_eb"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_eb.object', {
#             'object': obj
#         })