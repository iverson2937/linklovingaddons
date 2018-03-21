# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


# class LinklovingEmployee(http.Controller):
#     @http.route('/linkloving_employee/linkloving_employee/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_employee/linkloving_employee/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_employee.listing', {
#             'root': '/linkloving_employee/linkloving_employee',
#             'objects': http.request.env['linkloving_employee.linkloving_employee'].search([]),
#         })

#     @http.route('/linkloving_employee/linkloving_employee/objects/<model("linkloving_employee.linkloving_employee"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_employee.object', {
#             'object': obj
#         })
