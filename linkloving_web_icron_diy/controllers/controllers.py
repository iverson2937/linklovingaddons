# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingWebIcronDiy(http.Controller):
#     @http.route('/linkloving_web_icron_diy/linkloving_web_icron_diy/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_web_icron_diy/linkloving_web_icron_diy/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_web_icron_diy.listing', {
#             'root': '/linkloving_web_icron_diy/linkloving_web_icron_diy',
#             'objects': http.request.env['linkloving_web_icron_diy.linkloving_web_icron_diy'].search([]),
#         })

#     @http.route('/linkloving_web_icron_diy/linkloving_web_icron_diy/objects/<model("linkloving_web_icron_diy.linkloving_web_icron_diy"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_web_icron_diy.object', {
#             'object': obj
#         })
