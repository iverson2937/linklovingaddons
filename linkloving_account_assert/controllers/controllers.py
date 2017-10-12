# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountAssert(http.Controller):
#     @http.route('/linkloving_account_assert/linkloving_account_assert/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_assert/linkloving_account_assert/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_assert.listing', {
#             'root': '/linkloving_account_assert/linkloving_account_assert',
#             'objects': http.request.env['linkloving_account_assert.linkloving_account_assert'].search([]),
#         })

#     @http.route('/linkloving_account_assert/linkloving_account_assert/objects/<model("linkloving_account_assert.linkloving_account_assert"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_assert.object', {
#             'object': obj
#         })
