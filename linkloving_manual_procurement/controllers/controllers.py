# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingManualProcurement(http.Controller):
#     @http.route('/linkloving_manual_procurement/linkloving_manual_procurement/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_manual_procurement/linkloving_manual_procurement/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_manual_procurement.listing', {
#             'root': '/linkloving_manual_procurement/linkloving_manual_procurement',
#             'objects': http.request.env['linkloving_manual_procurement.linkloving_manual_procurement'].search([]),
#         })

#     @http.route('/linkloving_manual_procurement/linkloving_manual_procurement/objects/<model("linkloving_manual_procurement.linkloving_manual_procurement"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_manual_procurement.object', {
#             'object': obj
#         })
