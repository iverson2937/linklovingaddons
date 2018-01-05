# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingWebIcron(http.Controller):
#     @http.route('/linkloving_web_icron/linkloving_web_icron/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_web_icron/linkloving_web_icron/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_web_icron.listing', {
#             'root': '/linkloving_web_icron/linkloving_web_icron',
#             'objects': http.request.env['linkloving_web_icron.linkloving_web_icron'].search([]),
#         })

#     @http.route('/linkloving_web_icron/linkloving_web_icron/objects/<model("linkloving_web_icron.linkloving_web_icron"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_web_icron.object', {
#             'object': obj
#         })
