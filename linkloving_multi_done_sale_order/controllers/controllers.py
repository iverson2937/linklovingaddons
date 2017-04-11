# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingMultiDoneSaleOrder(http.Controller):
#     @http.route('/linkloving_multi_done_sale_order/linkloving_multi_done_sale_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_multi_done_sale_order/linkloving_multi_done_sale_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_multi_done_sale_order.listing', {
#             'root': '/linkloving_multi_done_sale_order/linkloving_multi_done_sale_order',
#             'objects': http.request.env['linkloving_multi_done_sale_order.linkloving_multi_done_sale_order'].search([]),
#         })

#     @http.route('/linkloving_multi_done_sale_order/linkloving_multi_done_sale_order/objects/<model("linkloving_multi_done_sale_order.linkloving_multi_done_sale_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_multi_done_sale_order.object', {
#             'object': obj
#         })
