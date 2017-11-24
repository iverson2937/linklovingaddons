# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountDashboard(http.Controller):
#     @http.route('/linkloving_account_dashboard/linkloving_account_dashboard/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_dashboard/linkloving_account_dashboard/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_dashboard.listing', {
#             'root': '/linkloving_account_dashboard/linkloving_account_dashboard',
#             'objects': http.request.env['linkloving_account_dashboard.linkloving_account_dashboard'].search([]),
#         })

#     @http.route('/linkloving_account_dashboard/linkloving_account_dashboard/objects/<model("linkloving_account_dashboard.linkloving_account_dashboard"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_dashboard.object', {
#             'object': obj
#         })
