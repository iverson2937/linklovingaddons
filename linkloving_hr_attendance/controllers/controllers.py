# -*- coding: utf-8 -*-
from odoo import http

# class LinklovinrHrAttendance(http.Controller):
#     @http.route('/linklovinr_hr_attendance/linklovinr_hr_attendance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linklovinr_hr_attendance/linklovinr_hr_attendance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linklovinr_hr_attendance.listing', {
#             'root': '/linklovinr_hr_attendance/linklovinr_hr_attendance',
#             'objects': http.request.env['linklovinr_hr_attendance.linklovinr_hr_attendance'].search([]),
#         })

#     @http.route('/linklovinr_hr_attendance/linklovinr_hr_attendance/objects/<model("linklovinr_hr_attendance.linklovinr_hr_attendance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linklovinr_hr_attendance.object', {
#             'object': obj
#         })