# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProjectIssueSheet(http.Controller):
#     @http.route('/linkloving_project_issue_sheet/linkloving_project_issue_sheet/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_project_issue_sheet/linkloving_project_issue_sheet/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_project_issue_sheet.listing', {
#             'root': '/linkloving_project_issue_sheet/linkloving_project_issue_sheet',
#             'objects': http.request.env['linkloving_project_issue_sheet.linkloving_project_issue_sheet'].search([]),
#         })

#     @http.route('/linkloving_project_issue_sheet/linkloving_project_issue_sheet/objects/<model("linkloving_project_issue_sheet.linkloving_project_issue_sheet"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_project_issue_sheet.object', {
#             'object': obj
#         })