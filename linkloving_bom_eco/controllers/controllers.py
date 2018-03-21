# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingBomEco(http.Controller):
#     @http.route('/linkloving_bom_eco/linkloving_bom_eco/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_bom_eco/linkloving_bom_eco/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_bom_eco.listing', {
#             'root': '/linkloving_bom_eco/linkloving_bom_eco',
#             'objects': http.request.env['linkloving_bom_eco.linkloving_bom_eco'].search([]),
#         })

#     @http.route('/linkloving_bom_eco/linkloving_bom_eco/objects/<model("linkloving_bom_eco.linkloving_bom_eco"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_bom_eco.object', {
#             'object': obj
#         })
