# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountParent(http.Controller):
#     @http.route('/linkloving_account_parent/linkloving_account_parent/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_parent/linkloving_account_parent/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_parent.listing', {
#             'root': '/linkloving_account_parent/linkloving_account_parent',
#             'objects': http.request.env['linkloving_account_parent.linkloving_account_parent'].search([]),
#         })

#     @http.route('/linkloving_account_parent/linkloving_account_parent/objects/<model("linkloving_account_parent.linkloving_account_parent"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_parent.object', {
#             'object': obj
#         })