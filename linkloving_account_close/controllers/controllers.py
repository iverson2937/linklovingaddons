# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountClose(http.Controller):
#     @http.route('/linkloving_account_close/linkloving_account_close/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_close/linkloving_account_close/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_close.listing', {
#             'root': '/linkloving_account_close/linkloving_account_close',
#             'objects': http.request.env['linkloving_account_close.linkloving_account_close'].search([]),
#         })

#     @http.route('/linkloving_account_close/linkloving_account_close/objects/<model("linkloving_account_close.linkloving_account_close"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_close.object', {
#             'object': obj
#         })