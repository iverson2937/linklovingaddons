# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProductCategoryInherit(http.Controller):
#     @http.route('/linkloving_product_category_inherit/linkloving_product_category_inherit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_product_category_inherit/linkloving_product_category_inherit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_product_category_inherit.listing', {
#             'root': '/linkloving_product_category_inherit/linkloving_product_category_inherit',
#             'objects': http.request.env['linkloving_product_category_inherit.linkloving_product_category_inherit'].search([]),
#         })

#     @http.route('/linkloving_product_category_inherit/linkloving_product_category_inherit/objects/<model("linkloving_product_category_inherit.linkloving_product_category_inherit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_product_category_inherit.object', {
#             'object': obj
#         })
