# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingRework(http.Controller):
#     @http.route('/linkloving_rework/linkloving_rework/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_rework/linkloving_rework/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_rework.listing', {
#             'root': '/linkloving_rework/linkloving_rework',
#             'objects': http.request.env['linkloving_rework.linkloving_rework'].search([]),
#         })

#     @http.route('/linkloving_rework/linkloving_rework/objects/<model("linkloving_rework.linkloving_rework"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_rework.object', {
#             'object': obj
#         })
