# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountInvoiceAjust(http.Controller):
#     @http.route('/linkloving_account_invoice_ajust/linkloving_account_invoice_ajust/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_invoice_ajust/linkloving_account_invoice_ajust/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_invoice_ajust.listing', {
#             'root': '/linkloving_account_invoice_ajust/linkloving_account_invoice_ajust',
#             'objects': http.request.env['linkloving_account_invoice_ajust.linkloving_account_invoice_ajust'].search([]),
#         })

#     @http.route('/linkloving_account_invoice_ajust/linkloving_account_invoice_ajust/objects/<model("linkloving_account_invoice_ajust.linkloving_account_invoice_ajust"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_invoice_ajust.object', {
#             'object': obj
#         })
