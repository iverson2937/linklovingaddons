# -*- coding: utf-8 -*-
from psycopg2._psycopg import OperationalError

from odoo import http
from odoo.http import request


class LinklovingCompanies(http.Controller):
    @http.route('/linkloving_web/create_order', auth='none', type='json', csrf=False)
    def ll_call_kw(self, **kw):
        db = request.jsonrequest.get("db")
        vals = request.jsonrequest.get("vals")
        request.session.db = db
        request.params["db"] = db
        try:
            partner = request.env["res.partner"].sudo().search([("sub_company", "=", "main")], limit=1)
            if partner:
                vals["partner_id"] = partner.id
            else:
                return {
                    "code": -3,
                    "msg": u"未设置下单公司"
                }
        except OperationalError:
            return {
                "code": -2,
                "msg": u"账套%s不存在" % db
            }
        try:
            order_line_vals = vals["order_line"]
            order_line = []
            for line in order_line_vals:
                default_code = line["default_code"]
                p_obj = request.env["product.product"].sudo().search([("default_code", "=", default_code)])
                one_line_val = {
                    'product_id': p_obj.id,
                    'product_uom': p_obj.uom_id.id,
                    'product_uom_qty': line["product_uom_qty"],
                    'price_unit': p_obj.pre_cost_cal(),
                }
                order_line.append([0, False, one_line_val])
            vals["order_line"] = order_line
            so = request.env["sale.order"].sudo().create(vals)
            return {
                'so': so.name,
                'so_id': so.id,
            }
        except Exception, e:
            return {
                "code": -1,
                "msg": u"创建订单出现异常,请联系管理员"
            }
