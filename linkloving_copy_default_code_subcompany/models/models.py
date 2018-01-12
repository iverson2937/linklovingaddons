# -*- coding: utf-8 -*-
import json

import requests

from odoo import models, fields, api
from odoo.exceptions import UserError


class WebsitePlanner(models.Model):
    _inherit = 'web.planner'

    @api.one
    def import_codes(self, validate_codes, product_type):
        product_cate = self.env["product.category"]
        product_tmpl = self.env["product.template"]
        not_found_list = []
        success_count = 0

        for code in validate_codes:
            categ_id = product_cate.name_search(code.get("category_name")[0][1], operator="=")

            if not categ_id:
                not_found_list.append(code)
            else:
                categ = product_cate.browse(categ_id[0][0])

                if product_type == 'ordering':  # 订单制
                    r_ids = [self.env.ref('stock.route_warehouse0_mto').id,
                             self.env.ref('purchase.route_warehouse0_buy').id]
                elif product_type == 'stocking':
                    r_ids = [self.env.ref('purchase.route_warehouse0_buy').id]
                route_ids = [(6, 0, r_ids)]
                code.update({
                    'categ_id': categ.id,
                    # 'route_ids': [(6, 0, [self.env.ref(rou).id for rou in code["routes"]])]
                    'route_ids': route_ids,
                    'sale_ok': True,
                    'purchase_ok': True
                })
                product_tmpl.create(code)
                success_count += 1
        return {
            'success_count': success_count,
            'not_found_list': not_found_list
        }

    @api.model
    def _get_planner_application(self):
        planner = super(WebsitePlanner, self)._get_planner_application()
        planner.append(['planner_copy_code', 'Website Code Copy'])
        return planner

    @api.model
    def _prepare_planner_copy_code_data(self):
        # sudo is needed to avoid error message when current user's company != sale_department company
        companies = self.env["sub.company.info"].search_read([], fields=["name"])
        return {
            'sub_companies': companies,
        }

    @api.multi
    def check_codes(self, copy_info):
        error_msg = None
        if not copy_info.get("default_codes"):
            error_msg = u'未输入料号'
        if not copy_info.get("company"):
            error_msg = u'未选择公司'
        if not copy_info:
            error_msg = u'未选择公司,未添加料号'
        if not error_msg:
            # 先排除系统重复的, 然后将剩余部分去子系统查询
            repeat_codes_list, not_exist_codes = self.get_repeat_codes(copy_info.get("default_codes"),
                                                                       repeat_type='default_code')
            response = self.request_to_check_codes(copy_info.get("company"), not_exist_codes)
            if response:
                exist_codes = response.get("exist_codes")
                repeat_codes_list_new, validate_codes_new = self.get_repeat_codes(exist_codes, repeat_type='name')
                error_codes = response.get("not_exist_codes")  # 子系统不存在的料号
                error_codes += repeat_codes_list  # 主系统料号重复的
                error_codes += repeat_codes_list_new  # 主系统产品名称重复的

                response.pop('not_exist_codes')
                response.update({
                    'error_codes': error_codes,
                    'exist_codes': validate_codes_new,
                })
                return response
            else:
                error_msg = u'未收到返回'
        return {
            'error_msg': error_msg
        }

    def get_repeat_codes(self, codes, repeat_type):
        if repeat_type == 'default_code':
            product_s = self.env["product.template"].search([('default_code', "in", codes)])
            repeat_codes = product_s.mapped("default_code")
            repeat_codes_list = [{'default_code': code, 'reason': u'料号与本系统重复'} for code in repeat_codes]
            not_exist_codes = list(set(codes).difference(set(repeat_codes)))  # 不存在的code
            return repeat_codes_list, not_exist_codes
        elif repeat_type == 'name':
            product_s = self.env["product.template"].search([('name', "in", map(lambda x: x.get("name"), codes))])
            repeat_codes = product_s.mapped("name")
            repeat_codes_list = [{'default_code': product.name,
                                  'reason': u'产品名称与本系统重复'} for product in product_s]

            for co in codes:
                if co.get("name") in repeat_codes:
                    codes.remove(co)
            return repeat_codes_list, codes


    def request_to_check_codes(self, company, default_codes):
        chose_company = self.env["sub.company.info"].browse(company)
        url, db, header = chose_company.get_request_info('/linkloving_web/check_codes')
        response = requests.post(url, data=json.dumps({
            "db": db,
            "vals": default_codes or [],
        }), headers=header)
        return self.handle_response(response)

    def handle_response(self, response):
        res_json = json.loads(response.content).get("result")
        res_error = json.loads(response.content).get("error")
        if res_json and res_json.get("code") < 0:
            raise UserError(res_json.get("msg"))
        if res_error:
            raise UserError(res_error.get("data").get("name") + res_error.get("data").get("message"))
        return res_json


class ProductCategoryExtend(models.Model):
    _inherit = 'product.category'

    @api.multi
    def full_name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]
