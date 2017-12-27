# -*- coding: utf-8 -*-
import json

# from linklovingaddons.linkloving_app_api.controllers.controllers import STATUS_CODE_OK, JsonResponse, LinklovingAppApi
from odoo import http, SUPERUSER_ID
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


class LinklovingOutsourceAppApi(http.Controller):
    @classmethod
    def CURRENT_USER(cls, force_admin=False):
        uid = request.jsonrequest.get("uid")
        if uid:
            return uid
        if not force_admin:
            return request.context.get("uid")
        else:
            return SUPERUSER_ID


    @http.route('/linkloving_app_api/get_outsourcing_order_by_state', type='json', auth="none", csrf=False, )
    def get_outsourcing_order_by_state(self, **kw):
        state = request.jsonrequest.get("state")
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")

        orders = request.env["outsourcing.process.order"].sudo().search_read([("state", "=", state)],
                                                                             limit=limit,
                                                                             offset=offset)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=orders)

    @http.route('/linkloving_app_api/change_outsourcing_order_state', type='json', auth="none", csrf=False, )
    def change_outsourcing_order_state(self, **kw):
        order_id = request.jsonrequest.get("order_id")
        qty_produced = request.jsonrequest.get("qty_produced")
        state = request.jsonrequest.get("state")
        # offset = request.context.get("offset")

        order = request.env["outsourcing.process.order"].sudo(LinklovingOutsourceAppApi.CURRENT_USER()).browse(order_id)
        order.qty_produced = qty_produced
        if state == 'draft_to_out_ing':
            order.action_draft_to_out()
        elif state == 'out_ing_to_done':
            order.action_out_to_done()

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=order.read())
