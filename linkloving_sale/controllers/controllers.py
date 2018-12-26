# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class RtOrderImport(http.Controller):
    @http.route('/rt_web/get_sale_order', auth='none', type='json', csrf=False, methods=['POST'])
    def get_sale_order(self, **kw):
        print 'ddddddddddddddddddddddd'
        db = request.jsonrequest.get("db")  # 所选账套
        request.session.db = db  # 设置账套
        request.params["db"] = db

        vals = request.jsonrequest.get("so_number")  # 需要查询的产品数据
        print vals

        sale_id = request.env["sale.order"].sudo().search([("name", "=", vals)])
        data_return = {}
        try:
            data_return.update({
                'partner_id': sale_id.partner_id.name,
                'partner_invoice_id': sale_id.partner_invoice_id.name,
                'partner_shipping_id': sale_id.partner_shipping_id.name,
                'confirmation_date': sale_id.confirmation_date,
                'pi_number': sale_id.pi_number,
                'tax_id':sale_id.tax_id.name,
                'date_order': sale_id.validity_date,
                'sale_note': sale_id.remark,
                'line_ids': [{
                    'product_id': line.product_id.name,
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'tax_id': line.tax_id.name,
                } for line in sale_id.order_line]
            })

        except Exception, e:
            return {
                "code": -2,
                "msg": u"出现异常 %s" % str(e)
            }
        return {
            "code": 1,
            'vals': data_return,
        }
