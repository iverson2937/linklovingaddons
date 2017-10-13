# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountPrepayment(http.Controller):
#     @http.route('/linkloving_account_prepayment/linkloving_account_prepayment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_prepayment/linkloving_account_prepayment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_prepayment.listing', {
#             'root': '/linkloving_account_prepayment/linkloving_account_prepayment',
#             'objects': http.request.env['linkloving_account_prepayment.linkloving_account_prepayment'].search([]),
#         })

#     @http.route('/linkloving_account_prepayment/linkloving_account_prepayment/objects/<model("linkloving_account_prepayment.linkloving_account_prepayment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_prepayment.object', {
#             'object': obj
#         })
