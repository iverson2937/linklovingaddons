# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountPurchase(http.Controller):
#     @http.route('/linkloving_account_purchase/linkloving_account_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_purchase/linkloving_account_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_purchase.listing', {
#             'root': '/linkloving_account_purchase/linkloving_account_purchase',
#             'objects': http.request.env['linkloving_account_purchase.linkloving_account_purchase'].search([]),
#         })

#     @http.route('/linkloving_account_purchase/linkloving_account_purchase/objects/<model("linkloving_account_purchase.linkloving_account_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_purchase.object', {
#             'object': obj
#         })
