# -*- coding: utf-8 -*-
from psycopg2._psycopg import OperationalError

from odoo import http
from odoo.http import request


class LinklovingCompanies(http.Controller):
    @http.route('/linkloving_web/precost_price', auth='none', type='json', csrf=False)
    def precost_price(self, **kw):
        db = request.jsonrequest.get("db")  # 所选账套
        request.session.db = db  # 设置账套
        request.params["db"] = db

        vals = request.jsonrequest.get("vals")  # 需要查询的产品数据
        discount_to_sub = request.jsonrequest.get("discount_to_sub")  # 折算率
        data_return = []
        for val in vals:
            default_code = val["default_code"]
            try:
                p_obj = request.env["product.product"].sudo().search([("default_code", "=", default_code)])
            except OperationalError:
                return {
                    "code": -2,
                    "msg": u"账套%s不存在" % db
                }
            if not p_obj:
                return {
                    "code": -4,
                    "msg": u"%s此料号在%s账套中找不到" % (default_code, db)
                }
            data_return.append((1, val["line_id"], {
                'line_id': val["line_id"],
                'price_unit': p_obj.pre_cost_cal() / discount_to_sub
            }))

        return {
            "code": 1,
            'order_line': data_return,
        }

    @http.route('/linkloving_web/create_order', auth='none', type='json', csrf=False)
    def ll_call_kw(self, **kw):
        db = request.jsonrequest.get("db")  # 所选账套
        vals = request.jsonrequest.get("vals")  # so的数据
        # discount_to_sub = request.jsonrequest.get("discount_to_sub")  # 折算率
        request.session.db = db  # 设置账套
        request.params["db"] = db
        try:  #获取下单公司信息
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
        try:#创建so
            order_line_vals = vals["order_line"]
            order_line = []
            # order_line_return = []  #往回传的line信息
            for line in order_line_vals:
                default_code = line["default_code"]
                p_obj = request.env["product.product"].sudo().search([("default_code", "=", default_code)])
                if not p_obj:
                    return {
                        "code": -4,
                        "msg": u"%s此料号在%s账套中找不到" % (default_code, db)
                    }
                # price_after_dis = p_obj.pre_cost_cal() / discount_to_sub
                one_line_val = {
                    'product_id': p_obj.id,
                    'product_uom': p_obj.uom_id.id,
                    'product_uom_qty': line["product_uom_qty"],
                    'price_unit': line["price_unit"],
                }
                # order_line_return.append((1, line["line_id"], {
                #     # 'line_id': line["line_id"],
                #     'price_unit': price_after_dis
                # }))
                order_line.append([0, False, one_line_val])
            vals["order_line"] = order_line
            so = request.env["sale.order"].sudo().create(vals)
            return {
                "code": 1,
                'so': so.name,
                'so_id': so.id,
                # 'order_line': order_line_return,
            }
        except Exception, e:
            return {
                "code": -1,
                "msg": u"创建订单出现异常, %s" % e.name if hasattr(e, "name") else '',
            }
