# -*- coding: utf-8 -*-
import base64
import json
import logging
from urllib2 import URLError

import time

import operator

import datetime

import jpush
import pytz
from pip import download

import odoo
import odoo.modules.registry

from odoo import fields
from odoo.osv import expression
from odoo.tools import float_compare, SUPERUSER_ID, werkzeug, os, safe_eval
from odoo.tools.translate import _
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, \
                      serialize_exception as _serialize_exception
from odoo.exceptions import AccessError, UserError


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

class LinklovingOAApi(http.Controller):
    # 获取供应商
    @http.route('/linkloving_oa_api/get_supplier', type='json', auth="none", csrf=False, cors='*')
    def get_supplier(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        if request.jsonrequest.get("id"):
            supplier_detail_object = request.env['res.partner'].sudo().browse(request.jsonrequest.get("id"))
            supplier_details = {}
            supplier_details["name"] = supplier_detail_object.name
            supplier_details["phone"] = supplier_detail_object.phone
            supplier_details["street"] = supplier_detail_object.street
            supplier_details["email"] = supplier_detail_object.email
            supplier_details["website"] = supplier_detail_object.website
            supplier_details["express_sample_record"] = supplier_detail_object.express_sample_record
            supplier_details["lang"] = supplier_detail_object.lang
            supplier_details["contracts_count"] = len(supplier_detail_object.child_ids)  #联系人&地址个数
            supplier_details["purchase_order_count"] = supplier_detail_object.purchase_order_count  #订单数量
            supplier_details["invoice"] = supplier_detail_object.supplier_invoice_count   #对账
            supplier_details["payment_count"] = supplier_detail_object.payment_count   #付款申请
            supplier_details["put_in_storage"] = request.env['stock.picking'].sudo().search_count([('partner_id', '=', request.jsonrequest.get("id")),('state','=','waiting_in')])   #入库

            return JsonResponse.send_response(STATUS_CODE_OK, res_data=supplier_details)


        feedbacks = request.env['res.partner'].sudo().search([('supplier', '=', True)],
                                                             limit=limit,
                                                             offset=offset,
                                                             order='id desc')
        json_list = []
        for feedback in feedbacks:
            json_list.append(self.supplier_feedback_to_json(feedback))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def supplier_feedback_to_json(self, feedback):
        data = {
            'internal_code': feedback.internal_code,
            'city': feedback.city,
            'company_name': feedback.commercial_company_name,
            'email': feedback.email,
            'phone': feedback.phone,
            'id': feedback.id
        }
        return data

    #获取采购订单
    @http.route('/linkloving_oa_api/get_po', type='json', auth="none", csrf=False, cors='*')
    def get_po(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        state = request.jsonrequest.get("state")

        #判断若传入了id则表示是要获取详细的orderlines
        if(request.jsonrequest.get("id")):
            po_detail_object = request.env['purchase.order'].sudo().browse(request.jsonrequest.get("id"))

            po_order_detail = {}
            po_order_detail['name'] = po_detail_object.name
            po_order_detail['data_order'] = po_detail_object.date_order   #单据日期
            po_order_detail['handle_date'] = po_detail_object.handle_date  #交期
            po_order_detail['tax'] = {
                'tax_id':po_detail_object.tax_id.name
            }
            po_order_detail['currency'] = {
                'currency_name':po_detail_object.currency_id.name,
            }  #币种
            po_order_detail['amount_untaxed'] = po_detail_object.amount_untaxed  # 未含税金额
            po_order_detail['amount_tax'] = po_detail_object.amount_tax  # 税金
            po_order_detail['amount_total'] = po_detail_object.amount_total  # 总计
            po_order_detail['product_count'] = po_detail_object.product_count  # 总数量
            po_order_detail['notes'] = po_detail_object.notes
            po_order_detail['order_lines'] = []
            po_order_lines = po_detail_object.order_line
            for order_line in po_order_lines:
                po_order_detail['order_lines'].append(
                    {'name': order_line.product_id.name_get()[0][1],
                     'product_uom': order_line.product_uom.name,
                     'specs': order_line.product_id.product_specs,
                     'price_unit': order_line.price_unit,   #单价
                     'product_qty': order_line.product_qty,   #数量
                     'price_subtotal': order_line.price_subtotal,  #小计
                     'qty_invoiced': order_line.qty_invoiced,  #开单数量
                     'qty_received': order_line.qty_received,  #已接收数量
                     'price_tax': order_line.taxes_id.name,    #税金
                     }
                )
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=po_order_detail)

        domain = [('state', '=', state)]
        if state == 'purchase':
            domain = [('state', 'in', ('to approval','done','purchase'))]
        PO_orders = request.env['purchase.order'].sudo().search(domain,
                                                                limit=limit,
                                                                offset=offset,
                                                                order='id desc')
        json_list = []
        for po_order in PO_orders:
            json_list.append(self.po_order_to_json(po_order))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def po_order_to_json(self, po_order):
        data = {
            'id': po_order.id,
            'name': po_order.name,
            'creater': po_order.create_uid.name,
            'supplier': po_order.partner_id.commercial_company_name,
            'status_light': po_order.status_light,
            'product_count': po_order.product_count, #总数量
            'amount_total': po_order.amount_total  #总金额
        }
        return data

    #采购退货
    @http.route('/linkloving_oa_api/get_prma', type='json', auth="none", csrf=False, cors='*')
    def get_prma(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        prma_lists = request.env['return.goods'].sudo().search([],
                                                    limit=limit,
                                                    offset=offset,
                                                    order='id desc')
        json_list = []
        for prma_list in prma_lists:
            json_list.append(self.prma_list_to_json(prma_list))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def prma_list_to_json(self,prma_list):
        data = {
            'id': prma_list.id,
            'name': prma_list.name,
            'date': prma_list.date,
            'supplier': prma_list.partner_id.display_name,
            'remark': prma_list.remark
        }
        return data