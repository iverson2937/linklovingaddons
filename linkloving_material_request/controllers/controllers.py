# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingMaterialRequest(http.Controller):
#     @http.route('/linkloving_material_request/linkloving_material_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_material_request/linkloving_material_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_material_request.listing', {
#             'root': '/linkloving_material_request/linkloving_material_request',
#             'objects': http.request.env['linkloving_material_request.linkloving_material_request'].search([]),
#         })

#     @http.route('/linkloving_material_request/linkloving_material_request/objects/<model("linkloving_material_request.linkloving_material_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_material_request.object', {
#             'object': obj
#         })