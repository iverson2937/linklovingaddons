# -*- coding: utf-8 -*-
from odoo import http

# class RubanInventory(http.Controller):
#     @http.route('/ruban_inventory/ruban_inventory/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ruban_inventory/ruban_inventory/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ruban_inventory.listing', {
#             'root': '/ruban_inventory/ruban_inventory',
#             'objects': http.request.env['ruban_inventory.ruban_inventory'].search([]),
#         })

#     @http.route('/ruban_inventory/ruban_inventory/objects/<model("ruban_inventory.ruban_inventory"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ruban_inventory.object', {
#             'object': obj
#         })