# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingPurchaseChargeUser(http.Controller):
#     @http.route('/linkloving_purchase_charge_user/linkloving_purchase_charge_user/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_purchase_charge_user/linkloving_purchase_charge_user/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_purchase_charge_user.listing', {
#             'root': '/linkloving_purchase_charge_user/linkloving_purchase_charge_user',
#             'objects': http.request.env['linkloving_purchase_charge_user.linkloving_purchase_charge_user'].search([]),
#         })

#     @http.route('/linkloving_purchase_charge_user/linkloving_purchase_charge_user/objects/<model("linkloving_purchase_charge_user.linkloving_purchase_charge_user"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_purchase_charge_user.object', {
#             'object': obj
#         })
