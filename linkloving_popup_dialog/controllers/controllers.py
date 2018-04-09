# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPopupDialog(http.Controller):
#     @http.route('/linkloving_popup_dialog/linkloving_popup_dialog/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_popup_dialog/linkloving_popup_dialog/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_popup_dialog.listing', {
#             'root': '/linkloving_popup_dialog/linkloving_popup_dialog',
#             'objects': http.request.env['linkloving_popup_dialog.linkloving_popup_dialog'].search([]),
#         })

#     @http.route('/linkloving_popup_dialog/linkloving_popup_dialog/objects/<model("linkloving_popup_dialog.linkloving_popup_dialog"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_popup_dialog.object', {
#             'object': obj
#         })
