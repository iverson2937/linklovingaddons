# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountReport(http.Controller):
#     @http.route('/linkloving_account_report/linkloving_account_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_report/linkloving_account_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_report.listing', {
#             'root': '/linkloving_account_report/linkloving_account_report',
#             'objects': http.request.env['linkloving_account_report.linkloving_account_report'].search([]),
#         })

#     @http.route('/linkloving_account_report/linkloving_account_report/objects/<model("linkloving_account_report.linkloving_account_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_report.object', {
#             'object': obj
#         })
