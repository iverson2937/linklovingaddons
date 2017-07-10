# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingNewBomUpdate(http.Controller):
#     @http.route('/linkloving_new_bom_update/linkloving_new_bom_update/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_new_bom_update/linkloving_new_bom_update/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_new_bom_update.listing', {
#             'root': '/linkloving_new_bom_update/linkloving_new_bom_update',
#             'objects': http.request.env['linkloving_new_bom_update.linkloving_new_bom_update'].search([]),
#         })

#     @http.route('/linkloving_new_bom_update/linkloving_new_bom_update/objects/<model("linkloving_new_bom_update.linkloving_new_bom_update"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_new_bom_update.object', {
#             'object': obj
#         })
