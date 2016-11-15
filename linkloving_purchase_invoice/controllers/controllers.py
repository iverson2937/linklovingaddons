# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPurchaseInvoice(http.Controller):
#     @http.route('/linkloving_purchase_invoice/linkloving_purchase_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_purchase_invoice/linkloving_purchase_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_purchase_invoice.listing', {
#             'root': '/linkloving_purchase_invoice/linkloving_purchase_invoice',
#             'objects': http.request.env['linkloving_purchase_invoice.linkloving_purchase_invoice'].search([]),
#         })

#     @http.route('/linkloving_purchase_invoice/linkloving_purchase_invoice/objects/<model("linkloving_purchase_invoice.linkloving_purchase_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_purchase_invoice.object', {
#             'object': obj
#         })