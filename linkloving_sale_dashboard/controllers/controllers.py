# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingSaleDashboard(http.Controller):
#     @http.route('/linkloving_sale_dashboard/linkloving_sale_dashboard/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_sale_dashboard/linkloving_sale_dashboard/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_sale_dashboard.listing', {
#             'root': '/linkloving_sale_dashboard/linkloving_sale_dashboard',
#             'objects': http.request.env['linkloving_sale_dashboard.linkloving_sale_dashboard'].search([]),
#         })

#     @http.route('/linkloving_sale_dashboard/linkloving_sale_dashboard/objects/<model("linkloving_sale_dashboard.linkloving_sale_dashboard"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_sale_dashboard.object', {
#             'object': obj
#         })
