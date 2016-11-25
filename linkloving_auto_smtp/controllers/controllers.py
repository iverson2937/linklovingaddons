# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAutoSmtp(http.Controller):
#     @http.route('/linkloving_auto_smtp/linkloving_auto_smtp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_auto_smtp/linkloving_auto_smtp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_auto_smtp.listing', {
#             'root': '/linkloving_auto_smtp/linkloving_auto_smtp',
#             'objects': http.request.env['linkloving_auto_smtp.linkloving_auto_smtp'].search([]),
#         })

#     @http.route('/linkloving_auto_smtp/linkloving_auto_smtp/objects/<model("linkloving_auto_smtp.linkloving_auto_smtp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_auto_smtp.object', {
#             'object': obj
#         })