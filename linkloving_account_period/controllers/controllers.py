# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountPeriod(http.Controller):
#     @http.route('/linkloving_account_period/linkloving_account_period/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_period/linkloving_account_period/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_period.listing', {
#             'root': '/linkloving_account_period/linkloving_account_period',
#             'objects': http.request.env['linkloving_account_period.linkloving_account_period'].search([]),
#         })

#     @http.route('/linkloving_account_period/linkloving_account_period/objects/<model("linkloving_account_period.linkloving_account_period"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_period.object', {
#             'object': obj
#         })
