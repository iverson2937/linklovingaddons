# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProduct(http.Controller):
#     @http.route('/linkloving_product/linkloving_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_product/linkloving_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_product.listing', {
#             'root': '/linkloving_product/linkloving_product',
#             'objects': http.request.env['linkloving_product.linkloving_product'].search([]),
#         })

#     @http.route('/linkloving_product/linkloving_product/objects/<model("linkloving_product.linkloving_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_product.object', {
#             'object': obj
#         })
