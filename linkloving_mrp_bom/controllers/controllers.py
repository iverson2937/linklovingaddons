# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingMrpBom(http.Controller):
#     @http.route('/linkloving_mrp_bom/linkloving_mrp_bom/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_mrp_bom/linkloving_mrp_bom/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_mrp_bom.listing', {
#             'root': '/linkloving_mrp_bom/linkloving_mrp_bom',
#             'objects': http.request.env['linkloving_mrp_bom.linkloving_mrp_bom'].search([]),
#         })

#     @http.route('/linkloving_mrp_bom/linkloving_mrp_bom/objects/<model("linkloving_mrp_bom.linkloving_mrp_bom"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_mrp_bom.object', {
#             'object': obj
#         })
