# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

#
# class NameCardApi(http.Controller):
#     @http.route('/linkloving_oa_api/get_company_by_name/', auth='none', type='json')
#     def get_company_by_name(self):
#         name = request.jsonrequest.get("name")
#         return name
# class LinklovingOaApi(http.Controller):
#     @http.route('/linkloving_oa_api/linkloving_oa_api/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_oa_api/linkloving_oa_api/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_oa_api.listing', {
#             'root': '/linkloving_oa_api/linkloving_oa_api',
#             'objects': http.request.env['linkloving_oa_api.linkloving_oa_api'].search([]),
#         })

#     @http.route('/linkloving_oa_api/linkloving_oa_api/objects/<model("linkloving_oa_api.linkloving_oa_api"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_oa_api.object', {
#             'object': obj
#         })
