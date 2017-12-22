# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountCustomerRefund(http.Controller):
#     @http.route('/linkloving_account_customer_refund/linkloving_account_customer_refund/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_customer_refund/linkloving_account_customer_refund/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_customer_refund.listing', {
#             'root': '/linkloving_account_customer_refund/linkloving_account_customer_refund',
#             'objects': http.request.env['linkloving_account_customer_refund.linkloving_account_customer_refund'].search([]),
#         })

#     @http.route('/linkloving_account_customer_refund/linkloving_account_customer_refund/objects/<model("linkloving_account_customer_refund.linkloving_account_customer_refund"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_customer_refund.object', {
#             'object': obj
#         })
