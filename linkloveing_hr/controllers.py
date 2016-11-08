# -*- coding: utf-8 -*-
from odoo import http

# class LinkloveHr(http.Controller):
#     @http.route('/linklove_hr/linklove_hr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linklove_hr/linklove_hr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linklove_hr.listing', {
#             'root': '/linklove_hr/linklove_hr',
#             'objects': http.request.env['linklove_hr.linklove_hr'].search([]),
#         })

#     @http.route('/linklove_hr/linklove_hr/objects/<model("linklove_hr.linklove_hr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linklove_hr.object', {
#             'object': obj
#         })