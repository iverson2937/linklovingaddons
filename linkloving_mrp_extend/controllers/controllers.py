# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingMrpExtend(http.Controller):
#     @http.route('/linkloving_mrp_extend/linkloving_mrp_extend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_mrp_extend/linkloving_mrp_extend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_mrp_extend.listing', {
#             'root': '/linkloving_mrp_extend/linkloving_mrp_extend',
#             'objects': http.request.env['linkloving_mrp_extend.linkloving_mrp_extend'].search([]),
#         })

#     @http.route('/linkloving_mrp_extend/linkloving_mrp_extend/objects/<model("linkloving_mrp_extend.linkloving_mrp_extend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_mrp_extend.object', {
#             'object': obj
#         })