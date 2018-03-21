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
from controllers import JsonResponse
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
            colum_nation_list.append({'name': nation_one.name, 'id': nation_one.id})
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=colum_nation_list)
        # return str(colum_nation_list)

    # 创建用户
    @http.route('/linkloving_oa_api/create_employee', type='json', auth='none', csrf=False, cors='*')
    def create_employee(self, **kw):

        request.jsonrequest['department_id'] = int(
            request.jsonrequest.get("department_id")) if request.jsonrequest.get("department_id") else False
        request.jsonrequest['nation'] = int(request.jsonrequest.get("nation")) if request.jsonrequest.get(
            "nation") else False

        request.jsonrequest['identification_A'] = request.jsonrequest.get("identification_A").split(',')[-1:][
            0] if request.jsonrequest.get("identification_A") else False
        request.jsonrequest['identification_B'] = request.jsonrequest.get("identification_B").split(',')[-1:][
            0] if request.jsonrequest.get("identification_B") else False
        request.jsonrequest['bank_card'] = request.jsonrequest.get("bank_card").split(',')[-1:][
            0] if request.jsonrequest.get("bank_card") else False
        request.jsonrequest['image'] = request.jsonrequest.get("image").split(',')[-1:][
            0] if request.jsonrequest.get("image") else False

        if request.jsonrequest.get('certificate_image_ids'):
            certificate_list = []
            for certificate_one in request.jsonrequest.get('certificate_image_ids'):
                experience_id = request.env['ir.attachment'].sudo(int(request.jsonrequest.get("edit_id"))).create({
                    'res_model': u'hr.employee',
                    'name': '',
                    'datas': certificate_one.split(',')[-1:][0],
                    'datas_fname': '',
                    'public': True,
                })
                certificate_list.append(experience_id.id)
                request.jsonrequest['certificate_image_ids'] = [(6, 0, certificate_list)]

        if request.jsonrequest.get("work_email"):
            request.jsonrequest['is_create_account'] = True

        department_manager = request.env['hr.department'].sudo().browse(int(request.jsonrequest.get('department_id')))
        request.jsonrequest['parent_id'] = department_manager.manager_id.id

        try:
            employee = request.env['hr.employee'].sudo(int(request.jsonrequest.get("edit_id"))).create(
                request.jsonrequest)
        except Exception, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={'body': u'创建失败' + e.name})

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.employee_to_json(employee))

    # 获取员工信息
    @http.route('/linkloving_oa_api/get_employee_info', type='json', auth='none', csrf=False, cors='*')
    def get_employee_info(self, **kw):
        id_list = request.jsonrequest.get("id_list")
        is_all = request.jsonrequest.get("is_all")
        data_list = []

        if is_all:
            employee_list = request.env['hr.employee'].sudo().search([])
            for employee_one in employee_list:
                data_list.append(self.employee_to_json(employee_one))
        else:
            for id_one in id_list:
                employee_one = request.env['hr.employee'].sudo().browse(id_one)
                data_list.append(self.employee_to_json(employee_one))

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data_list)

    # 修改用户
    @http.route('/linkloving_oa_api/update_employee', type='json', auth='none', csrf=False, cors='*')
    def update_employee(self, **kw):

        if request.jsonrequest.get('certificate_image_ids'):
            certificate_list = []
            for certificate_one in request.jsonrequest.get('certificate_image_ids'):
                if type(certificate_one) == int:
                    certificate_list.append(certificate_one)
                elif 'base64' in certificate_one:
                    experience_id = request.env['ir.attachment'].sudo(int(request.jsonrequest.get("edit_id"))).create({
                        'res_model': u'hr.employee',
                        'name': '',
                        'datas': certificate_one.split(',')[-1:][0],
                        'datas_fname': '',
                        'public': True,
                    })
                    certificate_list.append(experience_id.id)
            request.jsonrequest['certificate_image_ids'] = [(6, 0, certificate_list)]

        if request.jsonrequest.get("identification_A"):
            if 'base64' in request.jsonrequest.get("identification_A"):
                request.jsonrequest['identification_A'] = request.jsonrequest.get("identification_A").split(',')[-1:][
                    0] if request.jsonrequest.get("identification_A") else False
            elif not request.jsonrequest.get("identification_A"):
                request.jsonrequest['identification_A'] = False
            elif 'http' in request.jsonrequest.get("identification_A"):
                request.jsonrequest.pop('identification_A')

        if request.jsonrequest.get("image"):
            if 'base64' in request.jsonrequest.get("image"):
                request.jsonrequest['image'] = request.jsonrequest.get("image").split(',')[-1:][
                    0] if request.jsonrequest.get("image") else False
            elif not request.jsonrequest.get("image"):
                request.jsonrequest['image'] = False
            elif 'http' in request.jsonrequest.get("image"):
                request.jsonrequest.pop('image')

        if request.jsonrequest.get("identification_B"):
            if 'base64' in request.jsonrequest.get("identification_B"):
                request.jsonrequest['identification_B'] = request.jsonrequest.get("identification_B").split(',')[-1:][
                    0] if request.jsonrequest.get("identification_B") else False
            elif not request.jsonrequest.get("identification_B"):
                request.jsonrequest['identification_B'] = False
            elif 'http' in request.jsonrequest.get("identification_B"):
                request.jsonrequest.pop('identification_B')

        if request.jsonrequest.get("bank_card"):
            if 'base64' in request.jsonrequest.get("bank_card"):
                request.jsonrequest['bank_card'] = request.jsonrequest.get("bank_card").split(',')[-1:][
                    0] if request.jsonrequest.get("bank_card") else False
            elif not request.jsonrequest.get("bank_card"):
                request.jsonrequest['bank_card'] = False
            elif 'http' in request.jsonrequest.get("bank_card"):
                request.jsonrequest.pop('bank_card')

        if request.jsonrequest.get('work_experience_ids'):
            experience_data = [(0, 0, {
                "name": experience_one.name,
                "department": experience_one.department,
                "position": experience_one.position,
                "entry_time": experience_one.entry_time,
                "Leaving_time": experience_one.Leaving_time,
            }) for experience_one in request.jsonrequest.get('work_experience_ids')
                               ]
            request.jsonrequest['work_experience_ids'] = experience_data

        if request.jsonrequest.get('education_experience_ids'):
            education_data = [(0, 0, {
                "name": education_one.name,
                "attainment": education_one.department,
                "major": education_one.position,
                "entry_time": education_one.entry_time,
                "Leaving_time": education_one.Leaving_time,
            }) for education_one in request.jsonrequest.get('education_experience_ids')
                              ]
            request.jsonrequest['education_experience_ids'] = education_data

        if request.jsonrequest.get('nation'):
            request.jsonrequest['nation'] = int(request.jsonrequest.get("nation")) if request.jsonrequest.get(
                "nation") else False
        else:
            request.jsonrequest.pop('nation')

        if request.jsonrequest.get('department_id'):
            request.jsonrequest['department_id'] = int(
                request.jsonrequest.get("department_id")) if request.jsonrequest.get("department_id") else False
        else:
            request.jsonrequest.pop('department_id')

        if not request.jsonrequest.get('entry_date'):
            request.jsonrequest.pop('entry_date')
        if not request.jsonrequest.get('marital'):
            request.jsonrequest.pop('marital')
        if not request.jsonrequest.get('birthday'):
            request.jsonrequest.pop('birthday')

        if not request.jsonrequest.get("work_email"):
            request.jsonrequest.pop('work_email')

        if not request.jsonrequest.get("identification_id"):
            request.jsonrequest.pop('identification_id')

        if request.jsonrequest.get("id") and request.jsonrequest.get("edit_id"):
            employee = request.env['hr.employee'].sudo(int(request.jsonrequest.get("edit_id"))).browse(
                int(request.jsonrequest.get("id")))
            employee.write(request.jsonrequest)
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.employee_to_json(employee))
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "没有识别到员工或者登录用户"})


    @classmethod
    def employee_to_json(cls, employeebean):
        # user = request.env["res.users"].sudo().browse(visitBean.create_uid.id)
        if (employeebean.write_date):
            time_unque = employeebean.write_date.replace("-", "").replace(" ", "").replace(":", "")

        marital_data = ' '
        if employeebean.marital == 'single':
            marital_data = '单身'
        elif employeebean.marital == 'married':
            marital_data = '已婚'
        elif employeebean.marital == 'divorced':
            marital_data = '离异'
        elif employeebean.marital == 'widower':
            marital_data = '丧婚'

        productivity_data = ' '
        if employeebean.mining_productivity == 'fixed_work':
            productivity_data = '正式'
        elif employeebean.mining_productivity == 'dispatch_work':
            productivity_data = '派遣'
        elif employeebean.mining_productivity == 'practice_work':
            productivity_data = '实习'
        elif employeebean.mining_productivity == 'leaving_work':
            productivity_data = '离职'
        elif employeebean.mining_productivity == 'try_out_work':
            productivity_data = '试用'

        accumulation_data = ' '
        if employeebean.accumulation_fund == 'class_a':
            accumulation_data = '甲类'
        elif employeebean.accumulation_fund == 'class_b':
            accumulation_data = '乙类'
        elif employeebean.accumulation_fund == 'null':
            accumulation_data = '无'

        probation_data = ' '
        if employeebean.probation_period == 'half_month':
            probation_data = '半个月'
        elif employeebean.probation_period == 'one_month':
            probation_data = '一个月'
        elif employeebean.probation_period == 'two_month':
            probation_data = '两个月'
        elif employeebean.probation_period == 'three_month':
            probation_data = '三个月'

        education_data = []
        for education_one in employeebean.education_experience_ids:

            attainment_data = ' '
            if education_one.attainment == 'fixed_work':
                attainment_data = '高中'
            elif education_one.attainment == 'temp_work':
                attainment_data = '中专'
            elif education_one.attainment == 'part_time_work':
                attainment_data = '大专'
            elif education_one.attainment == 'part_time_work':
                attainment_data = '本科'
            elif education_one.attainment == 'part_time_work':
                attainment_data = '硕士'
            elif education_one.attainment == 'part_time_work':
                attainment_data = 'MBA'
            elif education_one.attainment == 'part_time_work':
                attainment_data = '博士'

            education_data.append({
                "name": education_one.name or '',
                "attainment": attainment_data,
                "major": education_one.major or '',
                "entry_time": education_one.entry_time or '',
                "Leaving_time": education_one.Leaving_time or '',
            })

        vals = {
            "probation_date": employeebean.probation_date or '',
            "probation_period": probation_data or '',
            "probation_period_id": employeebean.probation_period,
            "bank_card_opening_bank": employeebean.bank_card_opening_bank or '',
            "bank_card_num": employeebean.bank_card_num or '',
            "id": employeebean.id or '',
            "uid": employeebean.user_id.id or '',
            "english_name": employeebean.english_name or '',
            "work_card": employeebean.work_card or '',
            "nation": employeebean.nation.name or '',
            "nation_id": employeebean.nation.id or '',
            "now_address_home": employeebean.now_address_home or '',
            "emergency_contact_name": employeebean.emergency_contact_name or '',
            "emergency_contact_relation": employeebean.emergency_contact_relation or '',
            "emergency_contact_way": employeebean.emergency_contact_way or '',

            "work_experience_ids": [{
                                        "name": experience_one.name or '',
                                        "department": experience_one.department or '',
                                        "position": experience_one.position or '',
                                        "entry_time": experience_one.entry_time or '',
                                        "Leaving_time": experience_one.Leaving_time or '',
                                    } for experience_one in employeebean.work_experience_ids],

            "education_experience_ids": education_data,

            "identification_A": LinklovingEmployeeControllers.get_one_img_url(employeebean.id, 'hr.employee',
                                                                              'identification_A',
                                                                              time_unque) if employeebean.identification_A else '',
            "identification_B": LinklovingEmployeeControllers.get_one_img_url(employeebean.id, 'hr.employee',
                                                                              'identification_B',
                                                                              time_unque) if employeebean.identification_B else '',

            "image": LinklovingEmployeeControllers.get_one_img_url(employeebean.id, 'hr.employee',
                                                                   'image', time_unque),

            "bank_card": LinklovingEmployeeControllers.get_one_img_url(employeebean.id, 'hr.employee',
                                                                       'bank_card',
                                                                       time_unque) if employeebean.bank_card else '',

            "certificate_image_ids": LinklovingEmployeeControllers.get_many_img_url(
                employeebean.certificate_image_ids),

            "entry_date": employeebean.entry_date or '',
            "probation_begin_date": employeebean.probation_begin_date or '',
            "probation_end_date": employeebean.probation_end_date or '',
            "mining_productivity": productivity_data,
            "mining_productivity_id": employeebean.mining_productivity,
            "contract_begin_date": employeebean.contract_begin_date or '',
            "contract_end_date": employeebean.contract_end_date or '',
            "accumulation_fund": accumulation_data,
            "insurance_type": employeebean.insurance_type.name or '',
            "buy_balance": employeebean.buy_balance or 0,
            "pre_payment_reminding": employeebean.pre_payment_reminding or 0,
            "is_create_account": employeebean.is_create_account or '',
            "name": employeebean.name or '',
            "mobile_phone": employeebean.mobile_phone or '',
            "work_phone": employeebean.work_phone or '',
            "work_email": employeebean.work_email or '',
            "company_id": employeebean.company_id.name or '',
            "department_id": employeebean.department_id.name or '',
            "department_id_id": employeebean.department_id.id or '',
            # "job_id": employeebean.job_id,
            "parent_id": employeebean.parent_id.name or '',
            "calendar_id": employeebean.calendar_id.name or '',
            "gender": (
                          '男' if employeebean.gender == 'male' else '女') or '',
            "gender_id": employeebean.gender,

            "birthday": employeebean.birthday or '',
            "identification_id": employeebean.identification_id or '',
            "address_home_two": employeebean.address_home_two or '',
            "marital": marital_data or "",
            "marital_id": employeebean.marital or "",
            "card_num": employeebean.card_num or '',
            # "hr_job_ids": [emp.name for emp in employeebean.hr_job_ids],
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
