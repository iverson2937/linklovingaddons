# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProductMultiSelection(http.Controller):
#     @http.route('/linkloving_product_multi_selection/linkloving_product_multi_selection/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_product_multi_selection/linkloving_product_multi_selection/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_product_multi_selection.listing', {
#             'root': '/linkloving_product_multi_selection/linkloving_product_multi_selection',
#             'objects': http.request.env['linkloving_product_multi_selection.linkloving_product_multi_selection'].search([]),
#         })

#     @http.route('/linkloving_product_multi_selection/linkloving_product_multi_selection/objects/<model("linkloving_product_multi_selection.linkloving_product_multi_selection"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_product_multi_selection.object', {
#             'object': obj
#         })