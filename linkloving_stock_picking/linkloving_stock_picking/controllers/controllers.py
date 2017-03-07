# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingStockPicking(http.Controller):
#     @http.route('/linkloving_stock_picking/linkloving_stock_picking/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_stock_picking/linkloving_stock_picking/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_stock_picking.listing', {
#             'root': '/linkloving_stock_picking/linkloving_stock_picking',
#             'objects': http.request.env['linkloving_stock_picking.linkloving_stock_picking'].search([]),
#         })

#     @http.route('/linkloving_stock_picking/linkloving_stock_picking/objects/<model("linkloving_stock_picking.linkloving_stock_picking"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_stock_picking.object', {
#             'object': obj
#         })