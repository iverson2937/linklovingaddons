# -*- coding: utf-8 -*-
from psycopg2._psycopg import OperationalError

from odoo import http
from odoo.http import request


class LinklovingCopyDefaultCodeSubcompany(http.Controller):
    @http.route('/linkloving_web/check_codes', auth='none', type='json', csrf=False, methods=['POST'])
    def check_codes(self, **kw):
        db = request.jsonrequest.get("db")  # 所选账套
        codes = request.jsonrequest.get("vals")  # so的数据
        # discount_to_sub = request.jsonrequest.get("discount_to_sub")  # 折算率
        request.session.db = db  # 设置账套
        request.params["db"] = db
        try:  # 获取下单公司信息
            products = request.env["product.template"].sudo().search([("default_code", "in", codes)])
        except OperationalError:
            return {
                "code": -2,
                "msg": u"账套%s不存在" % db
            }
        try:
            exist_codes = products.mapped("default_code")
            # intersection
            not_exist_codes = list(set(codes).difference(set(exist_codes)))  # 不存在的code
            repeat_codes_list = [{'default_code': code, 'reason': u'不存在'} for code in not_exist_codes]
            products_list = products.read(fields=[])
            return {
                'code': 1,
                'exist_codes': products_list,
                'not_exist_codes': repeat_codes_list
            }
        except Exception, e:
            return {
                "code": -1,
                "msg": u"创建订单出现异常, %s" % e.name if hasattr(e, "name") else '',
            }
