# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAccountBudget(http.Controller):
#     @http.route('/linkloving_account_budget/linkloving_account_budget/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_account_budget/linkloving_account_budget/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_account_budget.listing', {
#             'root': '/linkloving_account_budget/linkloving_account_budget',
#             'objects': http.request.env['linkloving_account_budget.linkloving_account_budget'].search([]),
#         })

#     @http.route('/linkloving_account_budget/linkloving_account_budget/objects/<model("linkloving_account_budget.linkloving_account_budget"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_account_budget.object', {
#             'object': obj
#         })
