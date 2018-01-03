# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProductApprove(http.Controller):
#     @http.route('/linkloving_product_approve/linkloving_product_approve/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_product_approve/linkloving_product_approve/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_product_approve.listing', {
#             'root': '/linkloving_product_approve/linkloving_product_approve',
#             'objects': http.request.env['linkloving_product_approve.linkloving_product_approve'].search([]),
#         })

#     @http.route('/linkloving_product_approve/linkloving_product_approve/objects/<model("linkloving_product_approve.linkloving_product_approve"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_product_approve.object', {
#             'object': obj
#         })
