# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountInherit(http.Controller):
#     @http.route('/linkloving_account_inherit/linkloving_account_inherit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_inherit/linkloving_account_inherit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_inherit.listing', {
#             'root': '/linkloving_account_inherit/linkloving_account_inherit',
#             'objects': http.request.env['linkloving_account_inherit.linkloving_account_inherit'].search([]),
#         })

#     @http.route('/linkloving_account_inherit/linkloving_account_inherit/objects/<model("linkloving_account_inherit.linkloving_account_inherit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_inherit.object', {
#             'object': obj
#         })
