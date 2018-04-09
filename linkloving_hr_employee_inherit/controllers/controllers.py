# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingHrEmployeeInherit(http.Controller):
#     @http.route('/linkloving_hr_employee_inherit/linkloving_hr_employee_inherit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_hr_employee_inherit/linkloving_hr_employee_inherit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_hr_employee_inherit.listing', {
#             'root': '/linkloving_hr_employee_inherit/linkloving_hr_employee_inherit',
#             'objects': http.request.env['linkloving_hr_employee_inherit.linkloving_hr_employee_inherit'].search([]),
#         })

#     @http.route('/linkloving_hr_employee_inherit/linkloving_hr_employee_inherit/objects/<model("linkloving_hr_employee_inherit.linkloving_hr_employee_inherit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_hr_employee_inherit.object', {
#             'object': obj
#         })
