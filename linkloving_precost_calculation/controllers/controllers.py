# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPrecostCalculation(http.Controller):
#     @http.route('/linkloving_precost_calculation/linkloving_precost_calculation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_precost_calculation/linkloving_precost_calculation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_precost_calculation.listing', {
#             'root': '/linkloving_precost_calculation/linkloving_precost_calculation',
#             'objects': http.request.env['linkloving_precost_calculation.linkloving_precost_calculation'].search([]),
#         })

#     @http.route('/linkloving_precost_calculation/linkloving_precost_calculation/objects/<model("linkloving_precost_calculation.linkloving_precost_calculation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_precost_calculation.object', {
#             'object': obj
#         })
