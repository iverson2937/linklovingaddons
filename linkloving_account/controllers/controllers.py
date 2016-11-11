# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccount(http.Controller):
#     @http.route('/linkloving_account/linkloving_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account/linkloving_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account.listing', {
#             'root': '/linkloving_account/linkloving_account',
#             'objects': http.request.env['linkloving_account.linkloving_account'].search([]),
#         })

#     @http.route('/linkloving_account/linkloving_account/objects/<model("linkloving_account.linkloving_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account.object', {
#             'object': obj
#         })