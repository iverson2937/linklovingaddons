# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingMrpAutomaticPlan(http.Controller):
#     @http.route('/linkloving_mrp_automatic_plan/linkloving_mrp_automatic_plan/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_mrp_automatic_plan/linkloving_mrp_automatic_plan/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_mrp_automatic_plan.listing', {
#             'root': '/linkloving_mrp_automatic_plan/linkloving_mrp_automatic_plan',
#             'objects': http.request.env['linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan'].search([]),
#         })

#     @http.route('/linkloving_mrp_automatic_plan/linkloving_mrp_automatic_plan/objects/<model("linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_mrp_automatic_plan.object', {
#             'object': obj
#         })
