# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProcess(http.Controller):
#     @http.route('/linkloving_process/linkloving_process/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_process/linkloving_process/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_process.listing', {
#             'root': '/linkloving_process/linkloving_process',
#             'objects': http.request.env['linkloving_process.linkloving_process'].search([]),
#         })

#     @http.route('/linkloving_process/linkloving_process/objects/<model("linkloving_process.linkloving_process"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_process.object', {
#             'object': obj
#         })