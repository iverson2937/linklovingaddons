# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingSaleOrderImport(http.Controller):
#     @http.route('/linkloving_sale_order_import/linkloving_sale_order_import/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_sale_order_import/linkloving_sale_order_import/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_sale_order_import.listing', {
#             'root': '/linkloving_sale_order_import/linkloving_sale_order_import',
#             'objects': http.request.env['linkloving_sale_order_import.linkloving_sale_order_import'].search([]),
#         })

#     @http.route('/linkloving_sale_order_import/linkloving_sale_order_import/objects/<model("linkloving_sale_order_import.linkloving_sale_order_import"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_sale_order_import.object', {
#             'object': obj
#         })
