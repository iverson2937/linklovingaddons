# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProductGroup(http.Controller):
#     @http.route('/linkloving_product_group/linkloving_product_group/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_product_group/linkloving_product_group/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_product_group.listing', {
#             'root': '/linkloving_product_group/linkloving_product_group',
#             'objects': http.request.env['linkloving_product_group.linkloving_product_group'].search([]),
#         })

#     @http.route('/linkloving_product_group/linkloving_product_group/objects/<model("linkloving_product_group.linkloving_product_group"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_product_group.object', {
#             'object': obj
#         })
