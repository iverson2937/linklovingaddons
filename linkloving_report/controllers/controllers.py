# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingReport(http.Controller):
#     @http.route('/linkloving_report/linkloving_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_report/linkloving_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_report.listing', {
#             'root': '/linkloving_report/linkloving_report',
#             'objects': http.request.env['linkloving_report.linkloving_report'].search([]),
#         })

#     @http.route('/linkloving_report/linkloving_report/objects/<model("linkloving_report.linkloving_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_report.object', {
#             'object': obj
#         })
