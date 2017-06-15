# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingNewMrp(http.Controller):
#     @http.route('/linkloving_new_mrp/linkloving_new_mrp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_new_mrp/linkloving_new_mrp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_new_mrp.listing', {
#             'root': '/linkloving_new_mrp/linkloving_new_mrp',
#             'objects': http.request.env['linkloving_new_mrp.linkloving_new_mrp'].search([]),
#         })

#     @http.route('/linkloving_new_mrp/linkloving_new_mrp/objects/<model("linkloving_new_mrp.linkloving_new_mrp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_new_mrp.object', {
#             'object': obj
#         })
