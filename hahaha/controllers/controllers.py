# -*- coding: utf-8 -*-
from odoo import http

# class Hahaha(http.Controller):
#     @http.route('/hahaha/hahaha/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hahaha/hahaha/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hahaha.listing', {
#             'root': '/hahaha/hahaha',
#             'objects': http.request.env['hahaha.hahaha'].search([]),
#         })

#     @http.route('/hahaha/hahaha/objects/<model("hahaha.hahaha"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hahaha.object', {
#             'object': obj
#         })