# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPurchaseAuthority(http.Controller):
#     @http.route('/linkloving_purchase_authority/linkloving_purchase_authority/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_purchase_authority/linkloving_purchase_authority/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_purchase_authority.listing', {
#             'root': '/linkloving_purchase_authority/linkloving_purchase_authority',
#             'objects': http.request.env['linkloving_purchase_authority.linkloving_purchase_authority'].search([]),
#         })

#     @http.route('/linkloving_purchase_authority/linkloving_purchase_authority/objects/<model("linkloving_purchase_authority.linkloving_purchase_authority"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_purchase_authority.object', {
#             'object': obj
#         })
