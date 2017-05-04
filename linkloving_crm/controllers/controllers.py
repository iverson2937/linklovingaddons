# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingCrm(http.Controller):
#     @http.route('/linkloving_crm/linkloving_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_crm/linkloving_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_crm.listing', {
#             'root': '/linkloving_crm/linkloving_crm',
#             'objects': http.request.env['linkloving_crm.linkloving_crm'].search([]),
#         })

#     @http.route('/linkloving_crm/linkloving_crm/objects/<model("linkloving_crm.linkloving_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_crm.object', {
#             'object': obj
#         })