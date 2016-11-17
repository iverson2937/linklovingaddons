# -*- coding: utf-8 -*-
from odoo import http

# class LinklvingAutoReorderRule(http.Controller):
#     @http.route('/linklving_auto_reorder_rule/linklving_auto_reorder_rule/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linklving_auto_reorder_rule/linklving_auto_reorder_rule/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linklving_auto_reorder_rule.listing', {
#             'root': '/linklving_auto_reorder_rule/linklving_auto_reorder_rule',
#             'objects': http.request.env['linklving_auto_reorder_rule.linklving_auto_reorder_rule'].search([]),
#         })

#     @http.route('/linklving_auto_reorder_rule/linklving_auto_reorder_rule/objects/<model("linklving_auto_reorder_rule.linklving_auto_reorder_rule"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linklving_auto_reorder_rule.object', {
#             'object': obj
#         })