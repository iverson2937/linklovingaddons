# -*- coding: utf-8 -*-
from odoo import http


class LinklovingSaleData(http.Controller):
    @http.route('/sale_orders/', auth='public')
    def list(self, **kw):
        return http.request.render('linkloving_sale_data.sale_orders', {
            'root': '/sale_orders/',
            'objects': http.request.env['sale.order'].search([]),
        })
