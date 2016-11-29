# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingInvoiceWorkflow(http.Controller):
#     @http.route('/linkloving_invoice_workflow/linkloving_invoice_workflow/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_invoice_workflow/linkloving_invoice_workflow/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_invoice_workflow.listing', {
#             'root': '/linkloving_invoice_workflow/linkloving_invoice_workflow',
#             'objects': http.request.env['linkloving_invoice_workflow.linkloving_invoice_workflow'].search([]),
#         })

#     @http.route('/linkloving_invoice_workflow/linkloving_invoice_workflow/objects/<model("linkloving_invoice_workflow.linkloving_invoice_workflow"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_invoice_workflow.object', {
#             'object': obj
#         })