# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingTimesheets(http.Controller):
#     @http.route('/linkloving_timesheets/linkloving_timesheets/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_timesheets/linkloving_timesheets/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_timesheets.listing', {
#             'root': '/linkloving_timesheets/linkloving_timesheets',
#             'objects': http.request.env['linkloving_timesheets.linkloving_timesheets'].search([]),
#         })

#     @http.route('/linkloving_timesheets/linkloving_timesheets/objects/<model("linkloving_timesheets.linkloving_timesheets"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_timesheets.object', {
#             'object': obj
#         })
