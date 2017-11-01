# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProductQuery(http.Controller):
#     @http.route('/linkloving_product_query/linkloving_product_query/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_product_query/linkloving_product_query/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_product_query.listing', {
#             'root': '/linkloving_product_query/linkloving_product_query',
#             'objects': http.request.env['linkloving_product_query.linkloving_product_query'].search([]),
#         })

#     @http.route('/linkloving_product_query/linkloving_product_query/objects/<model("linkloving_product_query.linkloving_product_query"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_product_query.object', {
#             'object': obj
#         })
