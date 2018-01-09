# -*- coding: utf-8 -*-
import json

import requests

from odoo import models, fields, api
from odoo.exceptions import UserError


class WebsitePlanner(models.Model):
    _inherit = 'web.planner'

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
            repeat_codes_list, not_exist_codes = self.get_repeat_codes(copy_info.get("default_codes"))
            response = self.request_to_check_codes(copy_info.get("company"), not_exist_codes)
            if response:
                error_codes = response.get("not_exist_codes")
                error_codes += repeat_codes_list
                response.pop('not_exist_codes')
                response.update({
                    'error_codes': error_codes,
                })
                return response
            else:
                error_msg = u'未收到返回'
        return {
            'error_msg': error_msg
        }

    def get_repeat_codes(self, codes):
        product_s = self.env["product.template"].search([("default_code", "in", codes)])
        repeat_codes = product_s.mapped("default_code")
        repeat_codes_list = [{'default_code': code, 'reason': u'与本系统重复'} for code in repeat_codes]
        not_exist_codes = list(set(codes).difference(set(repeat_codes)))  # 不存在的code
        return repeat_codes_list, not_exist_codes

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