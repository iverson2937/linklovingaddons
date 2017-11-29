# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingWebsitePartner(http.Controller):
#     @http.route('/linkloving_website_partner/linkloving_website_partner/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_website_partner/linkloving_website_partner/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_website_partner.listing', {
#             'root': '/linkloving_website_partner/linkloving_website_partner',
#             'objects': http.request.env['linkloving_website_partner.linkloving_website_partner'].search([]),
#         })

#     @http.route('/linkloving_website_partner/linkloving_website_partner/objects/<model("linkloving_website_partner.linkloving_website_partner"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_website_partner.object', {
#             'object': obj
#         })
