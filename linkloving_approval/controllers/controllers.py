# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingApproval(http.Controller):
#     @http.route('/linkloving_approval/linkloving_approval/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_approval/linkloving_approval/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_approval.listing', {
#             'root': '/linkloving_approval/linkloving_approval',
#             'objects': http.request.env['linkloving_approval.linkloving_approval'].search([]),
#         })

#     @http.route('/linkloving_approval/linkloving_approval/objects/<model("linkloving_approval.linkloving_approval"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_approval.object', {
#             'object': obj
#         })
