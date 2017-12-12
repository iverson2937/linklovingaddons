# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountStock(http.Controller):
#     @http.route('/linkloving_account_stock/linkloving_account_stock/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_stock/linkloving_account_stock/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_stock.listing', {
#             'root': '/linkloving_account_stock/linkloving_account_stock',
#             'objects': http.request.env['linkloving_account_stock.linkloving_account_stock'].search([]),
#         })

#     @http.route('/linkloving_account_stock/linkloving_account_stock/objects/<model("linkloving_account_stock.linkloving_account_stock"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_stock.object', {
#             'object': obj
#         })
