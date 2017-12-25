# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPoCombineSubcompany(http.Controller):
#     @http.route('/linkloving_po_combine_subcompany/linkloving_po_combine_subcompany/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_po_combine_subcompany/linkloving_po_combine_subcompany/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_po_combine_subcompany.listing', {
#             'root': '/linkloving_po_combine_subcompany/linkloving_po_combine_subcompany',
#             'objects': http.request.env['linkloving_po_combine_subcompany.linkloving_po_combine_subcompany'].search([]),
#         })

#     @http.route('/linkloving_po_combine_subcompany/linkloving_po_combine_subcompany/objects/<model("linkloving_po_combine_subcompany.linkloving_po_combine_subcompany"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_po_combine_subcompany.object', {
#             'object': obj
#         })
