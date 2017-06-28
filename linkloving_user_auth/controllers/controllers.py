# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request

STATUS_CODE_OK = 1
STATUS_CODE_ERROR = -1


# 返回的json 封装
class JsonResponse(object):
    @classmethod
    def send_response(cls, res_code, res_msg='', res_data=None, jsonRequest=True):
        data_dic = {'res_code': res_code,
                    'res_msg': res_msg,}
        if res_data:
            data_dic['res_data'] = res_data
        if jsonRequest:
            return data_dic
        return json.dumps(data_dic)


class LinklovingUserAuth(http.Controller):
    @http.route('/linkloving_user_auth/get_department_by_parent', auth='none', type='json')
    def get_department_by_parent(self, **kw):
        parent_id = request.jsonrequest.get("parent_id")

        if parent_id:
            des = request.env["hr.department"].sudo().search([("parent_id", '=', parent_id)])

        else:
            des = request.env["hr.department"].sudo().search([("parent_id", '=', False)])

        des_list = []
        for de in des:
            des_list.append(LinklovingUserAuth.hr_department_to_json(de))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=des_list)

    @classmethod
    def hr_department_to_json(cls, de):
        employees = request.env["hr.employee"].sudo().search([("department_id", '=', de.id)])
        em_list = []
        for em in employees:
            em_list.append(LinklovingUserAuth.hr_employee_to_json(em))
        return {
            'department_id': de.id,
            'name': de.name or '',
            'employees': em_list,
        }

    @classmethod
    def hr_employee_to_json(cls, em):
        return {
            'employee_id': em.id,
            'work_email': em.work_email,
            'name': em.name,
        }
