# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingReturnGoods(http.Controller):
#     @http.route('/linkloving_return_goods/linkloving_return_goods/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_return_goods/linkloving_return_goods/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_return_goods.listing', {
#             'root': '/linkloving_return_goods/linkloving_return_goods',
#             'objects': http.request.env['linkloving_return_goods.linkloving_return_goods'].search([]),
#         })

#     @http.route('/linkloving_return_goods/linkloving_return_goods/objects/<model("linkloving_return_goods.linkloving_return_goods"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_return_goods.object', {
#             'object': obj
#         })