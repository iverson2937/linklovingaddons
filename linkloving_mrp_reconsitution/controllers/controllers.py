# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingMrpReconsitution(http.Controller):
#     @http.route('/linkloving_mrp_reconsitution/linkloving_mrp_reconsitution/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_mrp_reconsitution/linkloving_mrp_reconsitution/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_mrp_reconsitution.listing', {
#             'root': '/linkloving_mrp_reconsitution/linkloving_mrp_reconsitution',
#             'objects': http.request.env['linkloving_mrp_reconsitution.linkloving_mrp_reconsitution'].search([]),
#         })

#     @http.route('/linkloving_mrp_reconsitution/linkloving_mrp_reconsitution/objects/<model("linkloving_mrp_reconsitution.linkloving_mrp_reconsitution"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_mrp_reconsitution.object', {
#             'object': obj
#         })