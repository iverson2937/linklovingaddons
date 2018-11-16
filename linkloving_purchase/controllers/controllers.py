# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class RtOrderImport(http.Controller):
    @http.route('/rt_web/get_purchase_order', auth='none', type='json', csrf=False, methods=['POST'])
    def get_purchase_order(self, **kw):
        print 'ddddddddddddddddddddddd'
        db = request.jsonrequest.get("db")  # 所选账套
        request.session.db = db  # 设置账套
        request.params["db"] = db

        vals = request.jsonrequest.get("po_number")  # 需要查询的产品数据
        print vals

        purchase_id = request.env["purchase.order"].sudo().search([("name", "=", vals)])
        data_return = {}
        try:
            data_return.update({
                'partner_id': purchase_id.partner_id.name,
                'tax_id':purchase_id.tax_id.name,
                'date_planned': purchase_id.handle_date,
                'remark': purchase_id.remark,
                'line_ids': [{
                    'product_id': line.product_id.name,
                    'product_qty': line.product_qty,
                    'price_unit': line.price_unit,
                    'tax_id': line.taxes_id.name,
                } for line in purchase_id.order_line]
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
