# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingHrPurchaseApply(http.Controller):
#     @http.route('/linkloving_hr_purchase_apply/linkloving_hr_purchase_apply/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_hr_purchase_apply/linkloving_hr_purchase_apply/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_hr_purchase_apply.listing', {
#             'root': '/linkloving_hr_purchase_apply/linkloving_hr_purchase_apply',
#             'objects': http.request.env['linkloving_hr_purchase_apply.linkloving_hr_purchase_apply'].search([]),
#         })

#     @http.route('/linkloving_hr_purchase_apply/linkloving_hr_purchase_apply/objects/<model("linkloving_hr_purchase_apply.linkloving_hr_purchase_apply"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_hr_purchase_apply.object', {
#             'object': obj
#         })
