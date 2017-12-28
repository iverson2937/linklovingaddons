# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountTaxInherit(http.Controller):
#     @http.route('/linkloving_account_tax_inherit/linkloving_account_tax_inherit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_tax_inherit/linkloving_account_tax_inherit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_tax_inherit.listing', {
#             'root': '/linkloving_account_tax_inherit/linkloving_account_tax_inherit',
#             'objects': http.request.env['linkloving_account_tax_inherit.linkloving_account_tax_inherit'].search([]),
#         })

#     @http.route('/linkloving_account_tax_inherit/linkloving_account_tax_inherit/objects/<model("linkloving_account_tax_inherit.linkloving_account_tax_inherit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_tax_inherit.object', {
#             'object': obj
#         })
