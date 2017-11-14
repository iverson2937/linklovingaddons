# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingSupplierInfo(http.Controller):
#     @http.route('/linkloving_supplier_info/linkloving_supplier_info/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_supplier_info/linkloving_supplier_info/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_supplier_info.listing', {
#             'root': '/linkloving_supplier_info/linkloving_supplier_info',
#             'objects': http.request.env['linkloving_supplier_info.linkloving_supplier_info'].search([]),
#         })

#     @http.route('/linkloving_supplier_info/linkloving_supplier_info/objects/<model("linkloving_supplier_info.linkloving_supplier_info"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_supplier_info.object', {
#             'object': obj
#         })
