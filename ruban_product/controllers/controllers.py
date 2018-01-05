# -*- coding: utf-8 -*-
from odoo import http

# class RubanProduct(http.Controller):
#     @http.route('/ruban_product/ruban_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ruban_product/ruban_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ruban_product.listing', {
#             'root': '/ruban_product/ruban_product',
#             'objects': http.request.env['ruban_product.ruban_product'].search([]),
#         })

#     @http.route('/ruban_product/ruban_product/objects/<model("ruban_product.ruban_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ruban_product.object', {
#             'object': obj
#         })
