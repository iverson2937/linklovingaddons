# -*- coding: utf-8 -*-
from openerp import http

# class LinklovingPriceStandard(http.Controller):
#     @http.route('/linkloving_price_standard/linkloving_price_standard/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_price_standard/linkloving_price_standard/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_price_standard.listing', {
#             'root': '/linkloving_price_standard/linkloving_price_standard',
#             'objects': http.request.env['linkloving_price_standard.linkloving_price_standard'].search([]),
#         })

#     @http.route('/linkloving_price_standard/linkloving_price_standard/objects/<model("linkloving_price_standard.linkloving_price_standard"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_price_standard.object', {
#             'object': obj
#         })