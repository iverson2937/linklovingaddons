# -*- coding: utf-8 -*-
from odoo import http

class LinklovingWorkOrder(http.Controller):
    @http.route('/linkloving_work_order/linkloving_work_order/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/linkloving_work_order/linkloving_work_order/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('linkloving_work_order.listing', {
            'root': '/linkloving_work_order/linkloving_work_order',
            'objects': http.request.env['linkloving_work_order.linkloving_work_order'].search([]),
        })

    @http.route('/linkloving_work_order/linkloving_work_order/objects/<model("linkloving_work_order.linkloving_work_order"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('linkloving_work_order.object', {
            'object': obj
        })