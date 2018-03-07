# -*- coding: utf-8 -*-
import base64
import json
import logging
from urllib2 import URLError
import re
import time
import datetime

import operator

import datetime

import jpush
import pytz
from pip import download

import odoo
import odoo.modules.registry
from linklovingaddons.linkloving_oa_api.controllers.controllers import JsonResponse
from models import LinklovingGetImageUrl, JPushExtend

from odoo import fields
from odoo.osv import expression
from odoo.tools import float_compare, SUPERUSER_ID, werkzeug, os, safe_eval
from odoo.tools.translate import _
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception
from odoo.exceptions import AccessError, UserError
from pyquery import PyQuery as pq

STATUS_CODE_OK = 1
STATUS_CODE_ERROR = -1


class LinklovingEmployeeControllers(http.Controller):
    # 员工模块

    # 获取民族
    @http.route('/linkloving_oa_api/get_employee_list', type='json', auth='public', csrf=False, cors='*')
    def get_employee_list(self, **kw):
        nation_list = request.env['hr.nation'].search([])
        colum_nation_list = []
        for nation_one in nation_list:
            colum_nation_list.append({'name': nation_one.name})
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=colum_nation_list)
        # return str(colum_nation_list)

    # 创建用户
    @http.route('/linkloving_oa_api/create_employee', auth='none', csrf=False, cors='*')
    def create_employee(self, **kw):

        name = request.jsonrequest.get("name")
        english_name = request.jsonrequest.get("english_name")
        gender = request.jsonrequest.get("gender")
        nation = request.jsonrequest.get("nation")
        birthday = request.jsonrequest.get("birthday")
        identification_id = request.jsonrequest.get("identification_id")
        address_home_two = request.jsonrequest.get("address_home_two")
        now_address_home = request.jsonrequest.get("now_address_home")
        marital = request.jsonrequest.get("marital")
        work_phone = request.jsonrequest.get("work_phone")
        work_email = request.jsonrequest.get("work_email")
        department_id = request.jsonrequest.get("department_id")
        hr_job_ids = request.jsonrequest.get("hr_job_ids")
        identification_A = request.jsonrequest.get("identification_A")
        identification_B = request.jsonrequest.get("identification_B")

        vals = {
            "name": name,
            "english_name": english_name,
            "gender": gender,
            "nation": int(nation) if nation else False,
            "birthday": birthday,
            "identification_id": identification_id,
            "address_home_two": address_home_two,
            "now_address_home": now_address_home,
            "marital": marital,
            "work_phone": work_phone,
            "work_email": work_email,
            "department_id": int(department_id) if department_id else False,
            "hr_job_ids": [(6, 0, hr_job_ids)],
            "identification_A": identification_A,
            "identification_B": identification_B,

        }
        employee = request.env['hr.employee'].create(vals)

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.employee_to_json(employee))

    # # 修改用户 one
    # @http.route('/linkloving_oa_api/update_employee', auth='none', csrf=False, cors='*')
    # def update_employee(self, **kw):
    #     english_name = request.jsonrequest.get("english_name")
    #     work_card = request.jsonrequest.get("work_card")
    #     nation = request.jsonrequest.get("nation")
    #     now_address_home = request.jsonrequest.get("now_address_home")
    #     emergency_contact_name = request.jsonrequest.get("emergency_contact_name")
    #     emergency_contact_relation = request.jsonrequest.get("emergency_contact_relation")
    #     emergency_contact_way = request.jsonrequest.get("emergency_contact_way")
    #
    #     work_experience_ids = request.jsonrequest.get("work_experience_ids")  # 工作经验
    #
    #     education_experience_ids = request.jsonrequest.get("education_experience_ids")  # 教育经历
    #
    #     identification_A = request.jsonrequest.get("identification_A")
    #     identification_B = request.jsonrequest.get("identification_B")
    #     bank_card = request.jsonrequest.get("bank_card")
    #
    #     certificate_image_ids = request.jsonrequest.get("certificate_image_ids")  # 证书
    #
    #     entry_date = request.jsonrequest.get("entry_date")
    #     probation_begin_date = request.jsonrequest.get("probation_begin_date")
    #     probation_end_date = request.jsonrequest.get("probation_end_date")
    #     mining_productivity = request.jsonrequest.get("mining_productivity")
    #     contract_begin_date = request.jsonrequest.get("contract_begin_date")
    #     contract_end_date = request.jsonrequest.get("contract_end_date")
    #     accumulation_fund = request.jsonrequest.get("accumulation_fund")
    #     insurance_type = request.jsonrequest.get("insurance_type")
    #     buy_balance = request.jsonrequest.get("buy_balance")
    #     is_create_account = request.jsonrequest.get("is_create_account")
    #     name = request.jsonrequest.get("name")
    #     mobile_phone = request.jsonrequest.get("mobile_phone")
    #     work_phone = request.jsonrequest.get("work_phone")
    #     work_email = request.jsonrequest.get("work_email")
    #     company_id = request.jsonrequest.get("company_id")
    #     department_id = request.jsonrequest.get("department_id")
    #     job_id = request.jsonrequest.get("job_id")
    #     parent_id = request.jsonrequest.get("parent_id")
    #     calendar_id = request.jsonrequest.get("calendar_id")
    #     gender = request.jsonrequest.get("gender")
    #     birthday = request.jsonrequest.get("birthday")
    #     identification_id = request.jsonrequest.get("identification_id")
    #     address_home_two = request.jsonrequest.get("address_home_two")
    #     marital = request.jsonrequest.get("marital")
    #     card_num = request.jsonrequest.get("card_num")
    #     hr_job_ids = request.jsonrequest.get("hr_job_ids")
    #
    #     certificate_list = []
    #     for certificate_one in certificate_image_ids:
    #         experience_id = self.env['ir.attachment'].create({
    #             'res_model': u'hr.employee',
    #             'name': certificate_one.name,
    #             'datas': certificate_one.content,
    #             'datas_fname': certificate_one.satas_fname,
    #             'public': True,
    #         })
    #         certificate_list.append(experience_id.id)
    #
    #     experience_data = [(0, 0, {
    #         "name": experience_one.name,
    #         "department": experience_one.department,
    #         "position": experience_one.position,
    #         "entry_time": experience_one.entry_time,
    #         "Leaving_time": experience_one.Leaving_time,
    #     }) for experience_one in work_experience_ids
    #                        ]
    #
    #     education_data = [(0, 0, {
    #         "name": education_one.name,
    #         "attainment": education_one.department,
    #         "major": education_one.position,
    #         "entry_time": education_one.entry_time,
    #         "Leaving_time": education_one.Leaving_time,
    #     }) for education_one in education_experience_ids
    #                       ]
    #
    #     vals = {
    #         "english_name": english_name,
    #         "work_card": work_card,
    #         "nation": int(nation) if nation else False,
    #         "now_address_home": now_address_home,
    #         "emergency_contact_name": emergency_contact_name,
    #         "emergency_contact_relation": emergency_contact_relation,
    #         "emergency_contact_way": emergency_contact_way,
    #
    #         "work_experience_ids": experience_data,
    #
    #         "education_experience_ids": education_data,
    #
    #         "identification_A": identification_A,
    #         "identification_B": identification_B,
    #         "bank_card": bank_card,
    #
    #         "certificate_image_ids": [(6, 0, certificate_list)],
    #
    #         "entry_date": entry_date,
    #         "probation_begin_date": probation_begin_date,
    #         "probation_end_date": probation_end_date,
    #         "mining_productivity": mining_productivity,
    #         "contract_begin_date": contract_begin_date,
    #         "contract_end_date": contract_end_date,
    #         "accumulation_fund": accumulation_fund,
    #         "insurance_type": insurance_type,
    #         "buy_balance": buy_balance,
    #         "is_create_account": is_create_account,
    #         "name": name,
    #         "mobile_phone": mobile_phone,
    #         "work_phone": work_phone,
    #         "work_email": work_email,
    #         "company_id": int(company_id) if company_id else False,
    #         "department_id": int(department_id) if department_id else False,
    #         "job_id": job_id,
    #         "parent_id": int(parent_id) if parent_id else False,
    #         "calendar_id": int(calendar_id) if company_id else False,
    #         "gender": gender,
    #         "birthday": birthday,
    #         "identification_id": identification_id,
    #         "address_home_two": address_home_two,
    #         "marital": marital,
    #         "card_num": card_num,
    #         "hr_job_ids": [(6, 0, hr_job_ids)]
    #     }
    #
    #     # employee = request.env['hr.employee'].create(vals)
    #
    #     # return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.changeVisit_to_json(employee))
    #     return 'ok'

    @classmethod
    def employee_to_json(cls, employeebean):
        # user = request.env["res.users"].sudo().browse(visitBean.create_uid.id)
        if (employeebean.write_date):
            time_unque = employeebean.write_date.replace("-", "").replace(" ", "").replace(":", "")

        vals = {
            "english_name": employeebean.english_name,
            "work_card": employeebean.work_card,
            "nation": employeebean.nation.name,
            "now_address_home": employeebean.now_address_home,
            "emergency_contact_name": employeebean.emergency_contact_name,
            "emergency_contact_relation": employeebean.emergency_contact_relation,
            "emergency_contact_way": employeebean.emergency_contact_way,

            "work_experience_ids": [{
                                        "name": experience_one.name,
                                        "department": experience_one.department,
                                        "position": experience_one.position,
                                        "entry_time": experience_one.entry_time,
                                        "Leaving_time": experience_one.Leaving_time,
                                    } for experience_one in employeebean.work_experience_ids],

            "education_experience_ids": [{
                                             "name": education_one.name,
                                             "attainment": education_one.department,
                                             "major": education_one.position,
                                             "entry_time": education_one.entry_time,
                                             "Leaving_time": education_one.Leaving_time,
                                         } for education_one in employeebean.education_experience_ids],

            "identification_A": LinklovingEmployeeControllers.get_one_img_url(employeebean.id, 'hr.employee',
                                                                              'identification_A', time_unque),
            "identification_B": LinklovingEmployeeControllers.get_one_img_url(employeebean.id, 'hr.employee',
                                                                              'identification_B', time_unque),
            "bank_card": employeebean.bank_card,

            "certificate_image_ids": LinklovingEmployeeControllers.get_many_img_url(employeebean.certificate_image_ids),

            "entry_date": employeebean.entry_date,
            "probation_begin_date": employeebean.probation_begin_date,
            "probation_end_date": employeebean.probation_end_date,
            "mining_productivity": employeebean.mining_productivity,
            "contract_begin_date": employeebean.contract_begin_date,
            "contract_end_date": employeebean.contract_end_date,
            "accumulation_fund": employeebean.accumulation_fund,
            "insurance_type": employeebean.insurance_type,
            "buy_balance": employeebean.buy_balance,
            "is_create_account": employeebean.is_create_account,
            "name": employeebean.name,
            "mobile_phone": employeebean.mobile_phone,
            "work_phone": employeebean.work_phone,
            "work_email": employeebean.work_email,
            "company_id": employeebean.company_id,
            "department_id": employeebean.department_id,
            "job_id": employeebean.job_id,
            "parent_id": employeebean.parent_id,
            "calendar_id": employeebean.calendar_id,
            "gender": employeebean.gender,
            "birthday": employeebean.birthday,
            "identification_id": employeebean.identification_id,
            "address_home_two": employeebean.address_home_two,
            "marital": employeebean.marital,
            "card_num": employeebean.card_num,
        }
        return vals

    # 获取一张图片 Binary
    @classmethod
    def get_one_img_url(cls, visit_id, model, field, time_unque):
        url = '%sweb/image?model=%s&id=%s&field=%s&unique=%s' % (
            request.httprequest.host_url, model, str(visit_id), field, time_unque)
        return url

    # 获取 多张
    @classmethod
    def get_many_img_url(cls, data):
        imgs = []
        for data_one in data:
            url = '%sweb/image/%s' % (request.httprequest.host_url, str(data_one.id))
            imgs.append(url)
        return imgs
