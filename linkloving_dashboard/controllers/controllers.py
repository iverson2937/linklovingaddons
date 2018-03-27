# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingDashboard(http.Controller):
#     @http.route('/linkloving_dashboard/linkloving_dashboard/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_dashboard/linkloving_dashboard/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_dashboard.listing', {
#             'root': '/linkloving_dashboard/linkloving_dashboard',
#             'objects': http.request.env['linkloving_dashboard.linkloving_dashboard'].search([]),
#         })

#     @http.route('/linkloving_dashboard/linkloving_dashboard/objects/<model("linkloving_dashboard.linkloving_dashboard"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_dashboard.object', {
#             'object': obj
#         })
