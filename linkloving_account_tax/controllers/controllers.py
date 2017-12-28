# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountTax(http.Controller):
#     @http.route('/linkloving_account_tax/linkloving_account_tax/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_tax/linkloving_account_tax/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_tax.listing', {
#             'root': '/linkloving_account_tax/linkloving_account_tax',
#             'objects': http.request.env['linkloving_account_tax.linkloving_account_tax'].search([]),
#         })

#     @http.route('/linkloving_account_tax/linkloving_account_tax/objects/<model("linkloving_account_tax.linkloving_account_tax"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_tax.object', {
#             'object': obj
#         })
