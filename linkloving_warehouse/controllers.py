# -*- coding: utf-8 -*-
from openerp import http

# class LinklovingPurchase(http.Controller):
#     @http.route('/linkloving_purchase/linkloving_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_purchase/linkloving_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_purchase.listing', {
#             'root': '/linkloving_purchase/linkloving_purchase',
#             'objects': http.request.env['linkloving_purchase.linkloving_purchase'].search([]),
#         })

#     @http.route('/linkloving_purchase/linkloving_purchase/objects/<model("linkloving_purchase.linkloving_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_purchase.object', {
#             'object': obj
#         })
