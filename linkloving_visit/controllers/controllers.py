# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingVisit(http.Controller):
#     @http.route('/linkloving_visit/linkloving_visit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_visit/linkloving_visit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_visit.listing', {
#             'root': '/linkloving_visit/linkloving_visit',
#             'objects': http.request.env['linkloving_visit.linkloving_visit'].search([]),
#         })

#     @http.route('/linkloving_visit/linkloving_visit/objects/<model("linkloving_visit.linkloving_visit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_visit.object', {
#             'object': obj
#         })