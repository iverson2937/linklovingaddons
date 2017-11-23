# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingCustomRule(http.Controller):
#     @http.route('/linkloving_custom_rule/linkloving_custom_rule/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_custom_rule/linkloving_custom_rule/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_custom_rule.listing', {
#             'root': '/linkloving_custom_rule/linkloving_custom_rule',
#             'objects': http.request.env['linkloving_custom_rule.linkloving_custom_rule'].search([]),
#         })

#     @http.route('/linkloving_custom_rule/linkloving_custom_rule/objects/<model("linkloving_custom_rule.linkloving_custom_rule"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_custom_rule.object', {
#             'object': obj
#         })
