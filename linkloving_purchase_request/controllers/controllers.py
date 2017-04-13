# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPurchaseRequest(http.Controller):
#     @http.route('/linkloving_purchase_request/linkloving_purchase_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_purchase_request/linkloving_purchase_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_purchase_request.listing', {
#             'root': '/linkloving_purchase_request/linkloving_purchase_request',
#             'objects': http.request.env['linkloving_purchase_request.linkloving_purchase_request'].search([]),
#         })

#     @http.route('/linkloving_purchase_request/linkloving_purchase_request/objects/<model("linkloving_purchase_request.linkloving_purchase_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_purchase_request.object', {
#             'object': obj
#         })
