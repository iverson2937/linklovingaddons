# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request

STATUS_CODE_OK = 1
STATUS_CODE_ERROR = -1

#返回的json 封装
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

class LinklovingEb(http.Controller):
    @http.route('/linkloving_app_api/eb_order/get_eb_order_list', auth='none', type="json", crsf=False)
    def get_eb_order_list(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")

        orders = request.env["eb.order"].sudo().search([],limit=limit, offset=offset)
        orders_json = []
        for order in orders:
            orders_json.append(LinklovingEb.convert_eb_order_to_json(order))
        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=orders_json)


    @http.route('/linkloving_app_api/eb_order/create_eb_order', auth='none', type="json", crsf=False)
    def create_eb_order(self, **kw):
        eb_order_dic = request.jsonrequest.get("eb_order")

        eb_order = request.env["eb.order"].sudo().create(self.prepare_eb_order_values(eb_order_dic))

        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=LinklovingEb.convert_eb_order_to_json(eb_order))


    @http.route('/linkloving_app_api/eb_order/confirm_eb_order', auth='none', type="json", crsf=False)
    def confirm_eb_order(self, **kw):
        order_id =  request.jsonrequest.get("order_id")

        eb_order = request.env["eb.order"].sudo().search([("id", "=", order_id)], limit=1)
        eb_order.action_confirm()

        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=LinklovingEb.convert_eb_order_to_json(eb_order))

    def prepare_eb_order_values(self, dic):
        vals = {
            "name" : dic.get("order_name") or "",
            "eb_order_line_ids" : [(0, 0, {"qty" : line.get("qty"), "product_id" : line.get("product_id").get("product_id")}) for line in dic.get("eb_order_line_ids")]
        }
        return vals

    @classmethod
    def convert_eb_order_to_json(cls, order):
        data = {
            "order_id" : order.id,
            "order_name" : order.name,
            "is_finish_transfer" : order.is_finish_transfer,
            "create_date" : order.create_date,
            "eb_order_line_ids" : [{"product_id" : {"product_id" : order_line.product_id.id, "product_name" : order_line.product_id.display_name},"qty": order_line.qty}  for order_line in order.eb_order_line_ids]
        }
        return data
#     @http.route('/linkloving_eb/linkloving_eb/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_eb.listing', {
#             'root': '/linkloving_eb/linkloving_eb',
#             'objects': http.request.env['linkloving_eb.linkloving_eb'].search([]),
#         })

#     @http.route('/linkloving_eb/linkloving_eb/objects/<model("linkloving_eb.linkloving_eb"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_eb.object', {
#             'object': obj
#         })