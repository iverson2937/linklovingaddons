# -*- coding: utf-8 -*-
from psycopg2._psycopg import OperationalError

from odoo import http
from odoo.http import request


class LinklovingCopyDefaultCodeSubcompany(http.Controller):
    @http.route('/linkloving_web/check_codes', auth='none', type='json', csrf=False, methods=['POST'])
    def check_codes(self, **kw):
        db = request.jsonrequest.get("db")  # 所选账套
        codes = request.jsonrequest.get("vals")  # so的数据
        lang = request.jsonrequest.get("lang")
        # discount_to_sub = request.jsonrequest.get("discount_to_sub")  # 折算率
        request.session.db = db  # 设置账套
        request.params["db"] = db
        request.lang = lang
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

            routes = request.env["ir.model.data"].sudo().search([("model", "=", "stock.location.route")])
            products_list = []
            for p in products:
                p_routes = routes.filtered(lambda x: x.res_id in p.route_ids.ids)
                products_list.append({
                    'id': p.id,
                    'name': p.name,
                    'default_code': p.default_code or '',
                    'category_name': p.categ_id.full_name_get() or '',
                    'product_specs': p.product_specs or '',
                    'product_ll_type': p.product_ll_type,
                    'order_ll_type': p.order_ll_type,
                    'sale_ok': p.sale_ok,
                    'purchase_ok': p.purchase_ok,
                    'can_be_expensed': p.can_be_expensed,
                    'type': p.type,
                    # 'routes': [{'modules': rou.modules, 'name': rou.name} for rou in p_routes]
                    'routes': [rou.module + '.' + rou.name for rou in p_routes],
                    'inner_code': p.inner_code or '',
                    'inner_spec': p.inner_spec or '',
                })
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
