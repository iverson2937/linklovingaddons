# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingAppMenuControl(http.Controller):
#     @http.route('/linkloving_app_menu_control/linkloving_app_menu_control/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_app_menu_control/linkloving_app_menu_control/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_app_menu_control.listing', {
#             'root': '/linkloving_app_menu_control/linkloving_app_menu_control',
#             'objects': http.request.env['linkloving_app_menu_control.linkloving_app_menu_control'].search([]),
#         })

#     @http.route('/linkloving_app_menu_control/linkloving_app_menu_control/objects/<model("linkloving_app_menu_control.linkloving_app_menu_control"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_app_menu_control.object', {
#             'object': obj
#         })