# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPdm(http.Controller):
#     @http.route('/linkloving_pdm/linkloving_pdm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_pdm/linkloving_pdm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_pdm.listing', {
#             'root': '/linkloving_pdm/linkloving_pdm',
#             'objects': http.request.env['linkloving_pdm.linkloving_pdm'].search([]),
#         })

#     @http.route('/linkloving_pdm/linkloving_pdm/objects/<model("linkloving_pdm.linkloving_pdm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_pdm.object', {
#             'object': obj
#         })