# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class LinklovingStockPicking(http.Controller):
    @http.route('/payment/order_status_show', type='http', auth='public', website=True, methods=['GET'], csrf=False,
                cors='*')
    def order_status_show(self, **kw):
        ir_list = []
        if kw.get('pidsss'):
            ir_one = http.request.env['ir.attachment'].search([('id', '=', int(kw.get('pidsss')))])
            domain = []
            if ir_one.product_ir_img_id:
                domain = [('product_ir_img_id', '=', ir_one.product_ir_img_id.id)]
            elif ir_one.partner_img_id:
                domain = [('partner_img_id', '=', ir_one.partner_img_id.id)]

            ir_one_list = http.request.env['ir.attachment'].search(domain)

            ir_list = ir_one_list.ids

            print ir_one_list.ids

        values = {
            'transaction': kw.get('pidsss'),
            'list_ids': ir_list
        }
        return request.render("linkloving_stock_picking.order_status_show", values)
