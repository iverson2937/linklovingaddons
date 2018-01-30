# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingProductAttachment(http.Controller):
#     @http.route('/linkloving_product_attachment/linkloving_product_attachment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_product_attachment/linkloving_product_attachment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_product_attachment.listing', {
#             'root': '/linkloving_product_attachment/linkloving_product_attachment',
#             'objects': http.request.env['linkloving_product_attachment.linkloving_product_attachment'].search([]),
#         })

#     @http.route('/linkloving_product_attachment/linkloving_product_attachment/objects/<model("linkloving_product_attachment.linkloving_product_attachment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_product_attachment.object', {
#             'object': obj
#         })