# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPurchaseInvoiceDone(http.Controller):
#     @http.route('/linkloving_purchase_invoice_done/linkloving_purchase_invoice_done/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_purchase_invoice_done/linkloving_purchase_invoice_done/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_purchase_invoice_done.listing', {
#             'root': '/linkloving_purchase_invoice_done/linkloving_purchase_invoice_done',
#             'objects': http.request.env['linkloving_purchase_invoice_done.linkloving_purchase_invoice_done'].search([]),
#         })

#     @http.route('/linkloving_purchase_invoice_done/linkloving_purchase_invoice_done/objects/<model("linkloving_purchase_invoice_done.linkloving_purchase_invoice_done"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_purchase_invoice_done.object', {
#             'object': obj
#         })
