# -*- coding: utf-8 -*-
from odoo import http

# class LinklovingBleDevice(http.Controller):
#     @http.route('/linkloving_ble_device/linkloving_ble_device/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_ble_device/linkloving_ble_device/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_ble_device.listing', {
#             'root': '/linkloving_ble_device/linkloving_ble_device',
#             'objects': http.request.env['linkloving_ble_device.linkloving_ble_device'].search([]),
#         })

#     @http.route('/linkloving_ble_device/linkloving_ble_device/objects/<model("linkloving_ble_device.linkloving_ble_device"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_ble_device.object', {
#             'object': obj
#         })