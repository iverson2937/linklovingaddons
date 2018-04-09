# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingMoPlannedReport(http.Controller):
#     @http.route('/linkloving_mo_planned_report/linkloving_mo_planned_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_mo_planned_report/linkloving_mo_planned_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_mo_planned_report.listing', {
#             'root': '/linkloving_mo_planned_report/linkloving_mo_planned_report',
#             'objects': http.request.env['linkloving_mo_planned_report.linkloving_mo_planned_report'].search([]),
#         })

#     @http.route('/linkloving_mo_planned_report/linkloving_mo_planned_report/objects/<model("linkloving_mo_planned_report.linkloving_mo_planned_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_mo_planned_report.object', {
#             'object': obj
#         })
