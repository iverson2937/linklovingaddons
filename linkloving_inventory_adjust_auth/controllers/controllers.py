# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingInventoryAdjustAuth(http.Controller):
#     @http.route('/linkloving_inventory_adjust_auth/linkloving_inventory_adjust_auth/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_inventory_adjust_auth/linkloving_inventory_adjust_auth/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_inventory_adjust_auth.listing', {
#             'root': '/linkloving_inventory_adjust_auth/linkloving_inventory_adjust_auth',
#             'objects': http.request.env['linkloving_inventory_adjust_auth.linkloving_inventory_adjust_auth'].search([]),
#         })

#     @http.route('/linkloving_inventory_adjust_auth/linkloving_inventory_adjust_auth/objects/<model("linkloving_inventory_adjust_auth.linkloving_inventory_adjust_auth"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_inventory_adjust_auth.object', {
#             'object': obj
#         })
