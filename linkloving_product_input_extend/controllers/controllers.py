# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProductInputExtend(http.Controller):
#     @http.route('/linkloving_product_input_extend/linkloving_product_input_extend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_product_input_extend/linkloving_product_input_extend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_product_input_extend.listing', {
#             'root': '/linkloving_product_input_extend/linkloving_product_input_extend',
#             'objects': http.request.env['linkloving_product_input_extend.linkloving_product_input_extend'].search([]),
#         })

#     @http.route('/linkloving_product_input_extend/linkloving_product_input_extend/objects/<model("linkloving_product_input_extend.linkloving_product_input_extend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_product_input_extend.object', {
#             'object': obj
#         })
