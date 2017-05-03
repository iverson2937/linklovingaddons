# -*- coding: utf-8 -*-
import base64
import json
import os

import time

import datetime

import werkzeug
from pip import download

import odoo
from odoo import http
from odoo.addons.base.ir.ir_qweb import fields
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
        partner_id = request.jsonrequest.get("partner_id")
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")

        orders = request.env["eb.order"].sudo().search([("partner_id", "=", partner_id)], limit=limit, offset=offset)
        orders_json = []
        for order in orders:
            orders_json.append(LinklovingEb.convert_eb_order_to_json(order))
        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=orders_json)

    @http.route('/linkloving_app_api/eb_order/get_eb_shop_list', auth='none', type="json", crsf=False)
    def get_eb_shop_list(self, **kw):
        ds_team = request.env["crm.team"].sudo().search([("name", "=", "电商零售")], limit=1)
        partner_list = request.env["res.partner"].sudo().search([("team_id", "=", ds_team.id)])
        json_list = []
        for partner in partner_list:
            json_list.append(self.convert_partner_to_json(partner))
        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=json_list)

    def convert_partner_to_json(self, partner):
        return {
            "partner_id": partner.id,
            "name": partner.name or None,
        }

    @http.route('/linkloving_app_api/eb_order/get_today_eb_order', auth='none', type="json", crsf=False)
    def get_today_eb_order(self, **kw):
        partner_id = request.jsonrequest.get("partner_id")
        eb_order = request.env["eb.order"].sudo().search(
                [("my_create_date", "=", datetime.datetime.utcnow().strftime('%Y-%m-%d')),
                 ("state", "=", "draft"),
                 ("partner_id", "=", partner_id)], limit=1)
        if not eb_order:
            eb_order = request.env["eb.order"].sudo().create({
                "partner_id": partner_id,
            })
        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=LinklovingEb.convert_eb_order_to_json(eb_order))

    @http.route('/linkloving_app_api/eb_order/delete_eb_order_line', auth='none', type="json", crsf=False)
    def delete_eb_order_line(self, **kw):
        line_id = request.jsonrequest.get("line_id")
        line = request.env["eb.order.line"].sudo().search([("id", "=", line_id)], limit=1)
        if line:
            line.unlink()
        else:
            return JsonResponse.send_response(res_code=STATUS_CODE_ERROR,
                                              res_data={"error": u"条目id错误"})
        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data={})

    @http.route('/linkloving_app_api/eb_order/create_eb_order', auth='none', type="json", crsf=False)
    def create_eb_order(self, **kw):
        eb_order_dic = request.jsonrequest.get("eb_order")
        order_id = eb_order_dic.get("order_id")

        if not eb_order_dic or not order_id:
            return JsonResponse.send_response(res_code=STATUS_CODE_ERROR,
                                              res_data={"error" : "请检查参数"})
        eb_order = request.env["eb.order"].sudo().search([("id", "=", order_id)], limit=1)
        if eb_order:
            for line in eb_order_dic.get("eb_order_line_ids"):
                request.env["eb.order.line"].sudo().create({
                    "qty": line.get("qty"),
                    "product_id": line.get("product_id").get("product_product_id"),
                    "eb_order_id": eb_order.id
                })
        else:
            return JsonResponse.send_response(res_code=STATUS_CODE_ERROR,
                                              res_data={"error": "未找到今日的电商出货单"})

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
            "eb_order_line_ids": [
                (1, {"qty": line.get("qty"), "product_id": line.get("product_id").get("product_product_id")}) for line
                in dic.get("eb_order_line_ids")]
        }
        return vals

    @classmethod
    def convert_eb_order_to_json(cls, order):
        data = {
            "order_id" : order.id,
            "order_name" : order.name,
            "state" : order.state,
            "is_finish_transfer" : order.is_finish_transfer,
            "create_date": order.my_create_date,
            "eb_order_line_ids": [{"line_id": order_line.id, "product_id": {"product_id": order_line.product_id.id,
                                                                            "product_name": order_line.product_id.display_name},
                                   "qty": order_line.qty} for order_line in order.eb_order_line_ids],
            "partner_id": {
                "partner_id": order.partner_id.id,
                "name": order.partner_id.name,
            }
        }
        return data
#创建退货单
    @http.route('/linkloving_app_api/eb_refund_order/create_eb_refund_order', auth='none', type="json", crsf=False)
    def create_eb_refund_order(self, **kw):
        eb_refund_order_dic = request.jsonrequest.get("eb_refund_order")

        eb_order = request.env["eb.refund.order"].sudo().create(self.prepare_eb_refund_order_values(eb_refund_order_dic))
        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=LinklovingEb.convert_eb_refund_order_to_json(eb_order))

    @http.route('/linkloving_app_api/eb_refund_order/post_to_sale', auth='none', type="json", crsf=False)
    def post_to_sale(self, **kw):
        order_id = request.jsonrequest.get("order_id")
        state = request.jsonrequest.get("state")
        eb_refund_order = request.env["eb.refund.order"].sudo().search([("id", "=", order_id)], limit=1)
        if eb_refund_order:
            if state == "waiting_sale_confirm":#等待销售确认
                eb_refund_order.action_confirm()
            elif state == "confirmed":#已确认
                eb_refund_order.action_ok()
            else:
                return JsonResponse.send_response(res_code=STATUS_CODE_ERROR,
                                                  res_data={"error" : "错误的state参数"})
            return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=LinklovingEb.convert_eb_refund_order_to_json(eb_refund_order))
        else:
            return JsonResponse.send_response(res_code=STATUS_CODE_ERROR,
                                              res_data={"error": "错误的order_id参数"})



    def prepare_eb_refund_order_values(self, dic):

        vals = {
            "tracking_num": dic.get("tracking_num") or "",
            "refund_img": dic.get("refund_img"),
            "partner_id": dic.get("partner_id").get("partner_id") or None,
            "eb_refund_order_line_ids" : [(0, 0, {"qty" : line.get("qty"), "product_id" : line.get("product_id").get("product_product_id")}) for line in dic.get("eb_refund_order_line_ids")]
        }
        return vals


    @classmethod
    def convert_eb_refund_order_to_json(cls, order):
        data = {
            "order_id" : order.id,
            "tracking_num" : order.tracking_num,
            "partner_id":
                {
                    "partner_id": order.partner_id.id,
                    "name": order.partner_id.name,
                },
            "state" : order.state,
            "create_date" : order.create_date,
            "refund_img" : LinklovingEb.get_img_url(order.id, "eb.refund.order", "refund_img"),
            "eb_refund_order_line_ids" : [{"line_id" : order_line.id,"product_id" : {"product_id" : order_line.product_id.id, "product_name" : order_line.product_id.display_name},"qty": order_line.qty}  for order_line in order.eb_refund_order_line_ids]
        }
        return data

    @http.route('/linkloving_app_api/eb_refund_order/get_eb_refund_order_list', auth='none', type="json", crsf=False)
    def get_eb_refund_order_list(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        partner_id = request.jsonrequest.get("partner_id")

        orders = request.env["eb.refund.order"].sudo().search([("partner_id", "=", partner_id)], limit=limit,
                                                              offset=offset)
        orders_json = []
        for order in orders:
            orders_json.append(LinklovingEb.convert_eb_refund_order_to_json(order))
        return JsonResponse.send_response(res_code=STATUS_CODE_OK,
                                          res_data=orders_json)



    @classmethod
    def get_img_url(cls, id, model, field):
        url = '%slinkloving_app_api/get_image_url?id=%s&model=%s&field=%s&time=%s' % (
            request.httprequest.host_url, str(id), model, field, str(time.mktime(datetime.datetime.now().timetuple())))
        if not url:
            return ''
        return url

    @http.route('/linkloving_app_api/get_image_url', type='http', auth='none', csrf=False)
    def get_image_url_ccc(self, **kw):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        product_id = kw.get('id')
        model = kw.get('model')
        field = kw.get('field')
        status, headers, content = request.registry['ir.http'].binary_content(xmlid=None, model=model,
                                                                              id=product_id, field=field,
                                                                              unique=time.strftime(
                                                                                  DEFAULT_SERVER_DATE_FORMAT,
                                                                                  time.localtime()),
                                                                              default_mimetype='image/png',
                                                                              env=request.env(user=odoo.SUPERUSER_ID))
        if status == 304:
            return werkzeug.wrappers.Response(status=304, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200 and download:
            return request.not_found()

        if content:
            content = odoo.tools.image_resize_image(base64_source=content, size=(None, None),
                                                    encoding='base64', filetype='PNG')
            # resize force png as filetype
            headers = self.force_contenttype(headers, contenttype='image/png')

        if content:
            image_base64 = base64.b64decode(content)
        else:
            image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
            headers = self.force_contenttype(headers, contenttype='image/png')

        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        return response

    def placeholder(self, image='placeholder.png'):
        addons_path = http.addons_manifest['web']['addons_path']
        return open(os.path.join(addons_path, 'web', 'static', 'src', 'img', image), 'rb').read()

    def force_contenttype(self, headers, contenttype='image/png'):
        dictheaders = dict(headers)
        dictheaders['Content-Type'] = contenttype
        return dictheaders.items()