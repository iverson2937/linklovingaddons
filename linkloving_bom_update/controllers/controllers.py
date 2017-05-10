# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingBomUpdate(http.Controller):
#     @http.route('/linkloving_bom_update/linkloving_bom_update/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_bom_update/linkloving_bom_update/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_bom_update.listing', {
#             'root': '/linkloving_bom_update/linkloving_bom_update',
#             'objects': http.request.env['linkloving_bom_update.linkloving_bom_update'].search([]),
#         })

#     @http.route('/linkloving_bom_update/linkloving_bom_update/objects/<model("linkloving_bom_update.linkloving_bom_update"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_bom_update.object', {
#             'object': obj
#         })