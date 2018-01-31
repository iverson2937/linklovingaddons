# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingWarehousePickingReport(http.Controller):
#     @http.route('/linkloving_warehouse_picking_report/linkloving_warehouse_picking_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_warehouse_picking_report/linkloving_warehouse_picking_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_warehouse_picking_report.listing', {
#             'root': '/linkloving_warehouse_picking_report/linkloving_warehouse_picking_report',
#             'objects': http.request.env['linkloving_warehouse_picking_report.linkloving_warehouse_picking_report'].search([]),
#         })

#     @http.route('/linkloving_warehouse_picking_report/linkloving_warehouse_picking_report/objects/<model("linkloving_warehouse_picking_report.linkloving_warehouse_picking_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_warehouse_picking_report.object', {
#             'object': obj
#         })
