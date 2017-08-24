# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingStockAdjust(http.Controller):
#     @http.route('/linkloving_stock_adjust/linkloving_stock_adjust/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_stock_adjust/linkloving_stock_adjust/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_stock_adjust.listing', {
#             'root': '/linkloving_stock_adjust/linkloving_stock_adjust',
#             'objects': http.request.env['linkloving_stock_adjust.linkloving_stock_adjust'].search([]),
#         })

#     @http.route('/linkloving_stock_adjust/linkloving_stock_adjust/objects/<model("linkloving_stock_adjust.linkloving_stock_adjust"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_stock_adjust.object', {
#             'object': obj
#         })
