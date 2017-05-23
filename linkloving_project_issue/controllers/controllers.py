# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProjectIssue(http.Controller):
#     @http.route('/linkloving_project_issue/linkloving_project_issue/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_project_issue/linkloving_project_issue/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_project_issue.listing', {
#             'root': '/linkloving_project_issue/linkloving_project_issue',
#             'objects': http.request.env['linkloving_project_issue.linkloving_project_issue'].search([]),
#         })

#     @http.route('/linkloving_project_issue/linkloving_project_issue/objects/<model("linkloving_project_issue.linkloving_project_issue"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_project_issue.object', {
#             'object': obj
#         })