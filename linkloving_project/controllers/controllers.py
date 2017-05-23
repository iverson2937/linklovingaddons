# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProject(http.Controller):
#     @http.route('/linkloving_project/linkloving_project/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_project/linkloving_project/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_project.listing', {
#             'root': '/linkloving_project/linkloving_project',
#             'objects': http.request.env['linkloving_project.linkloving_project'].search([]),
#         })

#     @http.route('/linkloving_project/linkloving_project/objects/<model("linkloving_project.linkloving_project"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_project.object', {
#             'object': obj
#         })