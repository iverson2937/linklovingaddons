# -*- coding: utf-8 -*-
from linklovingaddons.linkloving_app_api.controllers.controllers import LinklovingAppApi, STATUS_CODE_OK
from linklovingaddons.linkloving_app_api.models import JsonResponse
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
import json

# 返回的json 封装
class JsonResponse(object):
    @classmethod
    def send_response(cls, res_code, res_msg='', res_data=None, jsonRequest=True):
        data_dic = {'res_code': res_code,
                    'res_msg': res_msg, }
        if res_data:
            data_dic['res_data'] = res_data
        if jsonRequest:
            return data_dic
        return json.dumps(data_dic)

class LinklovingTimesheets(http.Controller):
    # 分配二次加工负责人
    @http.route('/linkloving_timesheets/action_assign_secondary_operation_partner', type='json', auth='none',
                csrf=False)
    def action_assign_secondary_operation_partner(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        to_partner = request.jsonrequest.get("to_partner")

        if not to_partner or not picking_id:
            raise UserError(u"缺少必要的参数")
        picking = request.env['stock.picking'].sudo(LinklovingAppApi.CURRENT_USER()).browse(int(picking_id))
        if picking.timesheet_order_ids.filtered(lambda x: x.state == 'running'):
            raise UserError(u'已经有一个运行中的工时单')
        sheet = request.env["linkloving.timesheet.order"].sudo(LinklovingAppApi.CURRENT_USER()).create({
            'picking_id': picking_id,
            'to_partner': to_partner,
        })
        sheet.action_assign_partner()

        return JsonResponse.send_response(STATUS_CODE_OK, res_data={})

    # 分配二次加工负责人
    @http.route('/linkloving_timesheets/action_assign_hour_spent', type='json', auth='none', csrf=False)
    def action_assign_hour_spent(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        work_type_id = request.jsonrequest.get("work_type_id")
        hour_spent = request.jsonrequest.get("hour_spent")

        if not sheet_id or not picking_id or not work_type_id or not hour_spent:
            raise UserError(u"缺少必要的参数")

        sheet = request.env["linkloving.timesheet.order"].sudo(LinklovingAppApi.CURRENT_USER()).browse(sheet_id)
        if sheet_id.picking_id.id != picking_id:
            raise UserError(u'工时单与调拨单不对应,请重试')
        sheet.write({
            'work_type_id': work_type_id,
            'hour_spent': hour_spent,
        })
        sheet.action_assign_hour_spent()

        return JsonResponse.send_response(STATUS_CODE_OK, res_data={})

    @http.route('/linkloving_timesheets/get_work_type', type='json', auth='none', csrf=False)
    def get_work_type(self, **kw):
        # domain = [('state', '=', 'running')]
        bean_list = request.env['work.type'].sudo(LinklovingAppApi.CURRENT_USER()).search_read()
        data_list = []
        for bean in bean_list:
            data_list.append({
                'id': bean['id'],
                'name': bean['display_name']
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data_list)