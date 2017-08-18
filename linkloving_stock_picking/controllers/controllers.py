# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class LinklovingStockPicking(http.Controller):
    @http.route('/payment/order_status_show', type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def order_status_show(self, **params):


        print params.get('pidsss')


        values = {
            'transaction': '12',
            'order': 21
        }
        return request.render("linkloving_stock_picking.order_status_show", values)
