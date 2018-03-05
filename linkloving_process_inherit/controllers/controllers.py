# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProcessInherit(http.Controller):
#     @http.route('/linkloving_process_inherit/linkloving_process_inherit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_process_inherit/linkloving_process_inherit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_process_inherit.listing', {
#             'root': '/linkloving_process_inherit/linkloving_process_inherit',
#             'objects': http.request.env['linkloving_process_inherit.linkloving_process_inherit'].search([]),
#         })

#     @http.route('/linkloving_process_inherit/linkloving_process_inherit/objects/<model("linkloving_process_inherit.linkloving_process_inherit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_process_inherit.object', {
#             'object': obj
#         })
