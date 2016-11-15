# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingMrpSupplierSlover(http.Controller):
#     @http.route('/linkloving_mrp_supplier_slover/linkloving_mrp_supplier_slover/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_mrp_supplier_slover/linkloving_mrp_supplier_slover/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_mrp_supplier_slover.listing', {
#             'root': '/linkloving_mrp_supplier_slover/linkloving_mrp_supplier_slover',
#             'objects': http.request.env['linkloving_mrp_supplier_slover.linkloving_mrp_supplier_slover'].search([]),
#         })

#     @http.route('/linkloving_mrp_supplier_slover/linkloving_mrp_supplier_slover/objects/<model("linkloving_mrp_supplier_slover.linkloving_mrp_supplier_slover"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_mrp_supplier_slover.object', {
#             'object': obj
#         })