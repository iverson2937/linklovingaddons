# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.exceptions import UserError
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
    @http.route('/linkloving_user_auth/get_email_by_card_num', auth='none', type='json')
    def get_email_by_card_num(self, **kw):
        card_num = request.jsonrequest.get("card_num")
        old_emplyee = request.env["hr.employee"].sudo().search([("card_num", "=", card_num)])
        if old_emplyee:
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingUserAuth.hr_employee_to_json(old_emplyee))
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": u'未找到对应的用户信息,请联系管理员%d' % len(old_emplyee)})

    @http.route('/linkloving_user_auth/bind_nfc_card', auth='user', type='json')
    def bind_nfc_card(self, **kw):
        card_num = request.jsonrequest.get("card_num")
        employee_id = request.jsonrequest.get("employee_id")
        is_force = request.jsonrequest.get("is_force")
        employee = request.env["hr.employee"].browse(employee_id)
        old_emplyees = request.env["hr.employee"].search([("card_num", "=", card_num)])
        if is_force:
            old_emplyees.write({
                'card_num': False
            })
            employee.card_num = card_num
        else:
            if employee and not old_emplyees:  # 没有强制 并且没有其他用户的话 就直接绑定
                employee.card_num = card_num
            else:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={"error": u"已绑定员工:%s, 是否强制绑定" % (old_emplyees.name)})

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingUserAuth.hr_employee_to_json(employee))

    @http.route('/linkloving_user_auth/get_employee', auth='user', type='json')
    def get_employee(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        employees = request.env["hr.employee"].sudo().search([], limit=limit, offset=offset)
        em_list = []
        for em in employees:
            em_list.append(LinklovingUserAuth.hr_employee_to_json(em))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=em_list)

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

    # 是否有仓库权限
    @http.route('/linkloving_user_auth/auth_warehouse_manager', auth='none', type='json')
    def auth_warehouse_manager(self, **kw):
        card_num = request.jsonrequest.get("card_num")
        old_emplyee = request.env["hr.employee"].sudo().search([("card_num", "=", card_num)])
        if not card_num:
            raise UserError(u'此卡卡号为空')
        if old_emplyee:
            if len(old_emplyee) == 1:
                locations = request.env["stock.location"].sudo().search([])
                user_ids = locations.mapped("user_ids")
                if old_emplyee.user_id and old_emplyee.user_id.id in user_ids.ids:
                    return JsonResponse.send_response(STATUS_CODE_OK,
                                                      res_data=LinklovingUserAuth.hr_employee_to_json(old_emplyee))
                else:
                    return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": u"非仓库人员,请勿打卡"})
            else:
                raise UserError(u"该卡同时绑定了多个用户,请联系管理员")
        else:
            raise UserError(u'此卡未绑定任何用户')

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
            'work_email': em.work_email or '',
            'name': em.name,
            'card_num': em.card_num or '',
        }
