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
from linklovingaddons.linkloving_app_api.controllers.controllers import LinklovingAppApi
from models import JPushExtend

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


class LinklovingOAApi(http.Controller):
    # 供应商查询
    @http.route('/linkloving_oa_api/search_supplier', type='json', auth="none", csrf=False, cors='*')
    def search_supplier(self, **kw):
        name = request.jsonrequest.get("name")
        search_supplier_results = request.env['res.partner'].sudo().search(
            [("name", 'ilike', name), ('supplier', '=', True), ("is_company", '=', True)],
            limit=10,
            offset=0,
            order='id desc')
        json_list = []
        for feedback in search_supplier_results:
            json_list.append(self.supplier_feedback_to_json(feedback))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 获取供应商
    @http.route('/linkloving_oa_api/get_supplier', type='json', auth="none", csrf=False, cors='*')
    def get_supplier(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        if request.jsonrequest.get("id"):
            supplier_detail_object = request.env['res.partner'].sudo().browse(request.jsonrequest.get("id"))
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=self.supplier_detail_object_to_json(supplier_detail_object))

        feedbacks = request.env['res.partner'].sudo().search([('supplier', '=', True), ("is_company", '=', True)],
                                                             limit=limit,
                                                             offset=offset,
                                                             order='id desc')
        json_list = []
        for feedback in feedbacks:
            json_list.append(self.supplier_feedback_to_json(feedback))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def get_supplier_tags(self, objs):
        data = []
        for obj in objs:
            data.append(obj.display_name)
        return data

    def supplier_detail_object_to_json(self, supplier_detail_object):
        supplier_details = {
            "name": supplier_detail_object.name,
            "phone": supplier_detail_object.phone or '',
            "street": self.get_supplier_address(supplier_detail_object) or '',
            "email": supplier_detail_object.email or '',
            "website": supplier_detail_object.website or '',
            "express_sample_record": supplier_detail_object.express_sample_record or '',
            "lang": supplier_detail_object.lang,
            "contracts_count": len(supplier_detail_object.child_ids),  # 联系人&地址个数
            "contracts": self.get_contracts_in_supplier(supplier_detail_object.child_ids),
            'category': self.get_supplier_tags(supplier_detail_object.category_id),
            "purchase_order_count": supplier_detail_object.purchase_order_count,  # 订单数量
            "invoice": supplier_detail_object.supplier_invoice_count,  # 对账
            "payment_count": supplier_detail_object.payment_count,  # 付款申请
            "put_in_storage": request.env['stock.picking'].sudo().search_count(
                [('partner_id', '=', request.jsonrequest.get("id")), ('state', '=', 'waiting_in')]),
            # 入库
        }
        return supplier_details

    def get_supplier_address(self, obj):
        data = []
        data.append({
            'continent': (obj.continent.display_name or '') + (obj.country_id.display_name or '') + (
                obj.state_id.name or '') + (obj.city or '') + (obj.street2 or '') + (obj.street or ''),
        })
        return data

    def get_contracts_in_supplier(self, objs):
        json_lists = []

        for obj in objs:
            json_lists.append({
                "name": obj.name,
                "phone": obj.phone or '',
                "email": obj.email or '',
                "street": obj.street2 or '',
                "type": LinklovingOAApi.selection_get_map("res.partner", "type", obj.type),
            })
        return json_lists

    # 英文对应的中文一起传回
    @classmethod
    def selection_get_map(cls, res_model, field, value):
        field_detail = request.env[res_model].sudo().fields_get([field])
        for f in field_detail[field].get("selection"):
            if f[0] == value:
                return f
            else:
                continue
        return (value, value)

    @classmethod
    def selection_get(cls, res_model, field):
        field_detail = request.env[res_model].sudo().fields_get([field])
        return field_detail[field].get("selection")

    def supplier_feedback_to_json(self, feedback):
        data = {
            'internal_code': feedback.internal_code or '',
            'city': feedback.city or '',
            'company_name': feedback.commercial_company_name or '',
            'email': feedback.email or '',
            'phone': feedback.mobile or feedback.phone or '',
            'id': feedback.id or ''
        }
        return data

    # 获取采购订单
    @http.route('/linkloving_oa_api/get_po', type='json', auth="none", csrf=False, cors='*')
    def get_po(self, **kw):
        # 判断若传入了id则表示是要获取详细的orderlines
        if (request.jsonrequest.get("id")):
            po_detail_object = request.env['purchase.order'].sudo().browse(request.jsonrequest.get("id"))

            po_order_detail = {}
            po_order_detail['id'] = request.jsonrequest.get("id")
            po_order_detail['supplier'] = po_detail_object.partner_id.display_name
            po_order_detail['name'] = po_detail_object.name
            po_order_detail['data_order'] = po_detail_object.date_order  # 单据日期
            po_order_detail['handle_date'] = po_detail_object.handle_date  # 交期
            po_order_detail['tax'] = {
                'tax_id': po_detail_object.tax_id.name or ''
            }
            po_order_detail['currency'] = {
                'currency_name': po_detail_object.currency_id.name,
            }  # 币种
            po_order_detail['amount_untaxed'] = po_detail_object.amount_untaxed  # 未含税金额
            po_order_detail['amount_tax'] = po_detail_object.amount_tax  # 税金
            po_order_detail['amount_total'] = po_detail_object.amount_total  # 总计
            po_order_detail['product_count'] = po_detail_object.product_count  # 总数量
            po_order_detail['notes'] = po_detail_object.notes
            po_order_detail["origin"] = po_detail_object.origin  # 源单据
            # 交货及发票
            po_order_detail['date_planned'] = po_detail_object.date_planned  # 安排的日期
            po_order_detail['stock_to'] = po_detail_object.picking_type_id.display_name  # 交货到
            po_order_detail['incoterm_id'] = po_detail_object.incoterm_id.display_name or ''  # 贸易术语
            po_order_detail['invoice_status'] = LinklovingOAApi.selection_get_map("purchase.order", 'invoice_status',
                                                                                  po_detail_object.invoice_status),  # 账单状态
            po_order_detail['payment_term'] = po_detail_object.payment_term_id.display_name  # 付款条款
            po_order_detail['fiscal_position'] = po_detail_object.fiscal_position_id.display_name  # 财政状况

            po_order_detail['order_lines'] = []
            po_order_lines = po_detail_object.order_line
            for order_line in po_order_lines:
                po_order_detail['order_lines'].append(
                    {'name': order_line.product_id.name_get()[0][1],
                     'product_uom': order_line.product_uom.name,
                     'specs': order_line.product_id.product_specs,  # 规格
                     'price_unit': order_line.price_unit,  # 单价
                     'product_qty': order_line.product_qty,  # 数量
                     'price_subtotal': order_line.price_subtotal,  # 小计
                     'qty_invoiced': order_line.qty_invoiced,  # 开单数量
                     'qty_received': order_line.qty_received,  # 已接收数量
                     'price_tax': order_line.taxes_id.name,  # 税金
                     }
                )
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=po_order_detail)

        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        state = request.jsonrequest.get("state")
        domain = [('state', '=', state)]
        if state == 'purchase':
            domain = [('state', 'in', ('to approval', 'done', 'purchase'))]
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
            'order_line': po_order.order_line[0].product_id.display_name if po_order.order_line else '',
            'creater': po_order.create_uid.name,
            'supplier': po_order.partner_id.commercial_company_name or '',
            'status_light': po_order.status_light,
            'product_count': po_order.amount_total,  # 总数量
            'amount_total': po_order.product_count  # 总金额
        }
        return data

    # 采购退货
    @http.route('/linkloving_oa_api/get_prma', type='json', auth="none", csrf=False, cors='*')
    def get_prma(self, *kw):
        # 若传入id则获取详情
        if request.jsonrequest.get("id"):
            prma_detail_object = request.env['return.goods'].sudo().browse(request.jsonrequest.get("id"))
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=self.prma_detail_object_to_json(prma_detail_object))

        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        prma_lists = request.env['return.goods'].sudo().search([('supplier', '=', True)],
                                                               limit=limit,
                                                               offset=offset,
                                                               order='id desc')
        json_list = []
        for prma_list in prma_lists:
            json_list.append(self.prma_list_to_json(prma_list))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def prma_detail_object_to_json(self, prma_detail_object):
        prma_detail = {
            "name": prma_detail_object.name,
            "supplier": prma_detail_object.partner_id.display_name,
            "partner_invoice_add": prma_detail_object.partner_invoice_id.display_name,  # 开票地址
            "partner_shipping_add": prma_detail_object.partner_shipping_id.display_name,  # 退货地址
            "refer_po": prma_detail_object.purchase_id.name,  # 参考订单号
            "refer_po_amount_total": prma_detail_object.purchase_id.amount_total,  # 参考订单号的总金额
            "tracking_number": prma_detail_object.tracking_number or '',  # 物流信息
            "remark": prma_detail_object.remark or '',  # 退货原因
            "date": prma_detail_object.date,  # 退货日期
            "tax": prma_detail_object.tax_id.display_name or '',
            "amount_untaxed": prma_detail_object.amount_untaxed,  # 未含税金额
            "amount_tax": prma_detail_object.amount_tax,  # 税金
            "amount_total": prma_detail_object.amount_total,  # 总计
            "prma_line_products": self.prma_line_products_parse(prma_detail_object.line_ids)
        }
        return prma_detail

    # 具体的退货产品
    def prma_line_products_parse(self, objs):
        data = []
        for obj in objs:
            data.append({
                "name": obj.product_id.display_name,
                "uom": obj.product_uom.name,
                "invoice_status": LinklovingOAApi.selection_get_map("return.goods.line", 'invoice_status',
                                                                    obj.invoice_status),
                "product_uom_qty": obj.product_uom_qty,  # 退货数量
                "qty_delivered": obj.qty_delivered,  # 收到数量
                "price_unit": obj.price_unit,  # 单价
                "price_subtotal": obj.price_subtotal,  # 小计
                "qty_to_invoice": obj.qty_to_invoice,  # 待对账数量
            })
        return data

    def prma_list_to_json(self, prma_list):
        data = {
            'id': prma_list.id,
            'name': prma_list.name,
            'date': prma_list.date,
            'supplier': prma_list.partner_id.display_name,
            'remark': prma_list.remark or '',
            'amount_total': prma_list.amount_total
        }
        return data

    # 订单搜索
    @http.route('/linkloving_oa_api/search_purchase_order', type='json', auth="none", csrf=False, cors='*')
    def search_purchase_order(self, *kw):
        model = request.jsonrequest.get("model")
        name = request.jsonrequest.get("po_number")
        state = request.jsonrequest.get("state")
        if state == 'make_by_mrp':
            domain = [("name", 'ilike', name), ('state', '=', 'make_by_mrp')]
        elif state == 'purchase':
            domain = [("name", 'ilike', name),
                      ('state', 'not in', ('draft', 'sent', 'bid', 'confirmed', 'make_by_mrp'))]
        elif state == 'draft':
            domain = [("name", 'ilike', name), ('state', 'in', ('draft', 'sent', 'bid', 'cancel', 'confirmed'))]

        search_supplier_results = request.env[model].sudo().search(domain, limit=10, offset=0, order='id desc')
        json_list = []
        for feedback in search_supplier_results:
            if model == 'purchase.order':
                json_list.append(self.search_po_feedback_to_json(feedback))
            else:
                json_list.append(self.prma_list_to_json(feedback))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def search_po_feedback_to_json(self, feedback):
        data = {
            'name': feedback.name,
            'supplier': feedback.partner_id.display_name,
            'product_count': feedback.amount_total,  # 总数量
            'amount_total': feedback.product_count if feedback.product_count else '',  # 总金额
            'product': feedback.product_id.display_name,
            'state': LinklovingOAApi.selection_get_map("purchase.order", "state", feedback.state),
            'create': feedback.create_uid.display_name
        }
        return data

    # def search_prma_feedback_to_json(self, feedback):
    #     data = {
    #         'name': feedback.name,
    #         'supplier': feedback.partner_id.display_name,
    #         'date': feedback.date,
    #         'state': LinklovingOAApi.selection_get_map("return.goods", "state", feedback.state),
    #         'remark': feedback.remark
    #     }
    #     return data


    # 送货单详情页
    # 若是采购退货，除了id还要传一个prma  值随意
    @http.route('/linkloving_oa_api/get_delivery_notes', type='json', auth="none", csrf=False, cors='*')
    def get_delivery_notes(self, *kw):
        if request.jsonrequest.get("prma"):
            delivery_notes = request.env['return.goods'].sudo().browse(request.jsonrequest.get("id"))
        elif request.jsonrequest.get("receive"):
            delivery_notes = request.env['sale.order'].sudo().browse(request.jsonrequest.get("id"))
        else:
            delivery_notes = request.env['purchase.order'].sudo().browse(request.jsonrequest.get("id"))
        json_list = []
        for obj in delivery_notes.picking_ids:
            json_list.append(self.get_delivery_notes_details(obj))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def get_delivery_notes_details(self, obj):
        return {
            'id': obj.id,
            'name': obj.name,
            'partner': obj.partner_id.display_name,  # 合作伙伴
            'location_id': obj.location_id.display_name,  # 源位置区域
            'tracking_number': obj.tracking_number or '',  # 快递单号
            'is_emergency': obj.is_emergency or '',  # 加急
            'min_date': obj.min_date,  # 安排的日期
            'origin': obj.origin,  # 源单据
            'state': LinklovingOAApi.selection_get_map("stock.picking", "state", obj.state),
            'creater': obj.create_uid.display_name,
            'backorder': obj.backorder_id.display_name or '',  # 欠单于
            'move_type': LinklovingOAApi.selection_get_map("stock.picking", "move_type", obj.move_type),  # 交货类型
            'picking_type': obj.picking_type_id.display_name,  # 分拣类型
            'group': obj.group_id.display_name,  # 补货组
            'priority': LinklovingOAApi.selection_get_map("stock.picking", "priority", obj.priority),  # 优先级
            'carrier': obj.carrier_id.display_name or '',  # 承运商
            'carrier_tracking_ref': obj.carrier_tracking_ref or '',  # 跟踪参考
            'weight': obj.weight,  # 重量
            'shipping_weight': obj.shipping_weight,  # 航运重量
            'number_of_packages': obj.number_of_packages,  # 包裹件数
            'products': self.delivery_notes_products(obj.pack_operation_product_ids)
        }

    def delivery_notes_products(self, objs):
        data = []
        for obj in objs:
            data.append({
                'product_name': obj.product_id.display_name,
                'uom': obj.product_uom_id.name,  # 计量单位
                'to_loc': obj.to_loc,  # 至
                'from_loc': obj.from_loc,  # 从
                'ordered_qty': obj.ordered_qty,  # 待办
                'qty_done': obj.qty_done,  # 完成
            })
        return data

    # 送货单详情页-初始需求
    @http.route('/linkloving_oa_api/get_delivery_notes_initial_requ', type='json', auth="none", csrf=False, cors='*')
    def get_delivery_notes_initial_requ(self, *kw):
        initial_requs = request.env['stock.picking'].sudo().browse(request.jsonrequest.get("id"))
        json_list = []
        for obj in initial_requs.move_lines:
            json_list.append(self.get_dnir_details(obj))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def get_dnir_details(self, obj):
        return {
            'name': obj.name,
            'amount': obj.product_uom_qty,
            'uom': obj.product_uom.display_name,
            'state': LinklovingOAApi.selection_get_map("stock.picking", "state", obj.state),  # 优先级
        }

    # 联系电话
    @http.route('/linkloving_oa_api/get_contact_phone_number', type='json', auth="none", csrf=False, cors='*')
    def get_contact_phone_number(self, *kw):
        model = request.jsonrequest.get("model")
        po_object = request.env[model].sudo().browse(request.jsonrequest.get("id"))
        json_list = {
            "supplier": [{"name": po_object.partner_id.display_name or '', "phone": po_object.partner_id.phone or ''}],
            "creater": [{"name": po_object.create_uid.name,
                         "phone": po_object.create_uid.mobile or po_object.create_uid.phone or ''}],
        }
        json_list.update(self.get_all_phone_numbers())
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def get_all_phone_numbers(self):
        request.uid = SUPERUSER_ID
        pj_users = request.env.ref("linkloving_mrp_extend.group_charge_inspection").users
        ck_users = request.env.ref("linkloving_mrp_extend.group_charge_warehouse").users
        sc_users = request.env.ref("linkloving_mrp_extend.group_charge_produce").users
        data = {}
        data["pj"] = []
        data["ck"] = []
        data['sc'] = []
        for user in pj_users:
            data["pj"].append({
                'name': user.name,
                'phone': user.employee_ids[0].mobile_phone or '' if user.employee_ids else ''
            })
        for user in ck_users:
            data["ck"].append({
                'name': user.name,
                'phone': user.employee_ids[0].mobile_phone or '' if user.employee_ids else ''
            })
        for user in sc_users:
            data["sc"].append({
                'name': user.name,
                'phone': user.employee_ids[0].mobile_phone or '' if user.employee_ids else ''
            })
        return data

    # 对账-付款申请
    @http.route('/linkloving_oa_api/get_account_checking_lists_tab1', type='json', auth="none", csrf=False, cors='*')
    def get_account_checking_lists_tab1(self, *kw):
        # 若传入了id  获取详情页
        if (request.jsonrequest.get("id")):
            payment_request_detail_object = request.env['account.payment.register'].sudo().browse(
                request.jsonrequest.get("id"))
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.payment_request_detail_object_parse(
                payment_request_detail_object))

        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        payment_request_lists = request.env['account.payment.register'].sudo().search([('payment_type', '=', '1')],
                                                                                      limit=limit,
                                                                                      offset=offset,
                                                                                      order='id desc')
        json_list = []
        for payment_request_list in payment_request_lists:
            json_list.append(self.payment_request_list_to_json(payment_request_list))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def payment_request_list_to_json(self, obj):
        data = {
            'name': obj.name,
            'create_date': obj.create_date,
            'amount': obj.amount,
            'partner_name': obj.partner_id.display_name,
            'creater': obj.create_uid.display_name,
            'remark': obj.remark or '',
            'state': LinklovingOAApi.selection_get_map("account.payment.register", "state", obj.state),
            'id': obj.id
        }
        return data

    def payment_request_detail_object_parse(self, obj):
        return {
            'name': obj.name,
            'supplier': obj.partner_id.display_name,
            'bank': obj.bank_id.display_name,
            'amount': obj.amount,
            'receive_date': obj.receive_date,
            'remark': obj.remark or '',
            'supplier_account_check': self.get_supplier_account_check(obj.invoice_ids)
        }

    def get_supplier_account_check(self, objs):
        data = []
        for obj in objs:
            data.append({
                'supplier': obj.partner_id.display_name,
                'number': obj.number,
                'date_invoice': obj.date_invoice,  # 开票日期
                'date_due': obj.date_due or '',  # 截止日期
                'remain_apply_balance': obj.remain_apply_balance,  # 待申请付款金额
                'name': obj.name,
                'residual': obj.residual,  # 待支付
                'amount_total': obj.amount_total,  # 总计
                'state': LinklovingOAApi.selection_get_map("account.invoice", "state", obj.state)
            })
        return data

    # 对账-供应商账单、退货对账单
    @http.route('/linkloving_oa_api/get_account_checking_lists_tab2', type='json', auth="none", csrf=False, cors='*')
    def get_account_checking_lists_tab2(self, *kw):
        # 若传入了id  则获取详情页
        if request.jsonrequest.get("id"):
            bill_detail_object = request.env['account.invoice'].sudo().browse(request.jsonrequest.get("id"))
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=self.bill_detail_object_parse(bill_detail_object))

        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        type = request.jsonrequest.get("type")  # 供应商账单in_invoice   退货对账单in_refund
        bill_lists = request.env['account.invoice'].sudo().search([('type', '=', type)],
                                                                  limit=limit,
                                                                  offset=offset,
                                                                  order='id desc')
        json_list = []
        for bill_list in bill_lists:
            json_list.append(self.bill_list_to_json(bill_list))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def bill_detail_object_parse(self, obj):
        return {
            'supllier': obj.partner_id.display_name,  # 供应商
            'deduct_amount': obj.deduct_amount,  # 扣款
            'po': obj.po_id.display_name,  # 采购单
            'origin': obj.origin,  # 源单据
            'amount_untaxed': obj.amount_untaxed,  # 未含税金额
            'amount_tax': obj.amount_tax,  # 税金
            'amount_total': obj.amount_tax,  # 总计
            'date_invoice': obj.date_invoice or '',  # 账单日期
            'date_due': obj.date_due or '',  # 截止日期
            'reference': obj.reference or '',  # 供应商参考
            'payments': self.get_payment_ids(obj.payment_ids) or '',  # 付款申请单
            'remark': obj.remark or '',  # 备注
            'currency': obj.currency_id.name,  # 币种
            # 'payments_widget': obj.payments_widget if obj.payments_widget else '',  #已付金额
            'residual': obj.residual if obj.residual is not None else '',  # 截止金额
            'bill_detail_lists': self.get_bill_detail_lists(obj.invoice_line_ids)
        }

    def get_payment_ids(self, objs):
        data = []
        for obj in objs:
            data.append(obj.name)
        return data

    def get_bill_detail_lists(self, objs):
        data = []
        for obj in objs:
            data.append({
                'id': obj.id,
                'product': obj.product_id.display_name,  # 产品
                'explain': obj.name,  # 说明
                'price_unit': obj.price_unit,  # 单价
                'price_unit_o': obj.price_unit_o,  # original price
                'uom': obj.uom_id.display_name,
                'subject': obj.account_id.display_name,  # 科目
                'quantity': obj.quantity,
                'price_subtotal': obj.price_subtotal,  # 金额
                'tax': obj.invoice_line_tax_ids.name,  # 税金
            })
        return data

    def bill_list_to_json(self, obj):
        data = {
            'client': obj.partner_id.display_name,
            'date_invoice': obj.date_invoice or '',
            'number': obj.number,
            'date_due': obj.date_due or '',
            # 'commercial_partner': obj.commercial_partner_id.display_name,
            'state': LinklovingOAApi.selection_get_map("account.invoice", "state", obj.state),
            'origin': obj.origin or '',
            'residual_signed': obj.residual_signed,  # 待支付
            'amount_total_signed': obj.amount_total_signed,  # 总计
            'remain_apply_balance': obj.remain_apply_balance,  # 待申请付款金额
            'id': obj.id
        }
        return data

    # 对账-order lines
    @http.route('/linkloving_oa_api/get_order_lines', type='json', auth="none", csrf=False, cors='*')
    def get_order_lines(self, *kw):
        Order_Lines = request.env['account.invoice'].sudo().browse(request.jsonrequest.get("id"))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.get_account_checking_order_line(Order_Lines.order_line))

    def get_account_checking_order_line(self, objs):
        data = []
        for obj in objs:
            data.append({
                'explain': obj.name,  # 说明
                'supplier': obj.partner_id.display_name,
                'order': obj.order_id.display_name,  # 订单关联
                'product': obj.product_id.display_name,  # 产品
                'price_unit': obj.price_unit,  # 单价
                'product_qty': obj.product_qty,  # 数量
                'price_total': obj.price_total,  # 小计
                'date_planned': obj.date_planned,
                'uom': obj.product_uom.name
            })
        return data

    # 对账-其他信息  税说明
    @http.route('/linkloving_oa_api/get_account_checking_order_lines', type='json', auth="none", csrf=False, cors='*')
    def get_account_checking_order_lines(self, *kw):
        Data_Object = request.env['account.invoice'].sudo().browse(request.jsonrequest.get("id"))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.get_account_checking_more_message(Data_Object))

    def get_account_checking_more_message(self, obj):
        return {
            'journal': obj.journal_id.display_name,
            'user': obj.user_id.display_name,
            'account': obj.account_id.display_name,  # 科目
            'fiscal': obj.fiscal_position_id.display_name or '',
            'date': obj.date or '',
            'tax_lines': self.get_account_checking_taxs(obj.tax_line_ids)
        }

    def get_account_checking_taxs(self, objs):
        data = []
        for obj in objs:
            data.append({
                'explain': obj.display_name,
                'amount': obj.amount,
                'account': obj.account_id.display_name
            })
        return data

    # -----------销售部分-----------#
    # 线索
    @http.route('/linkloving_oa_api/get_clues', type='json', auth="none", csrf=False, cors='*')
    def get_clues(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get("user_id")
        clues = request.env['crm.lead'].sudo().search([('type', '=', 'lead' or False), ('user_id', '=', user_id)],
                                                      limit=limit,
                                                      offset=offset,
                                                      order='id desc')
        data = []
        for clue in clues:
            data.append({
                'id': clue.id,
                'name': clue.name,
                'contact_name': clue.contact_name or '',
                'team': clue.team_id.display_name,
                'user': clue.user_id.display_name,
                'category': self.get_supplier_tags(clue.partner_id.category_id),
                'priority': clue.priority,
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 线索详情
    @http.route('/linkloving_oa_api/get_clue_details', type='json', auth="none", csrf=False, cors='*')
    def get_clue_details(self, *kw):
        id = request.jsonrequest.get("id")
        obj = request.env['crm.lead'].sudo().browse(id)
        data = {
            'name': obj.name,
            'country': obj.country_id.display_name or '',
            'street': obj.street or '',
            'phone': obj.phone or '',
            'crm_source_id': obj.crm_source_id.display_name or '',
            'team': obj.team_id.display_name or '',
            'saler': obj.user_id.display_name or '',
            'tags': self.get_supplier_tags(obj.tag_ids),
            'description': obj.description or '',
            'contact_name': obj.contact_name or '',
            'email_from': obj.email_from or '',
            'function': obj.function or ''
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 线索搜索
    @http.route('/linkloving_oa_api/search_clues', type='json', auth="none", csrf=False, cors='*')
    def search_clues(self, **kw):
        name = request.jsonrequest.get("name")
        user_id = request.jsonrequest.get("user_id")
        if user_id == 1:
            domain = [("name", 'ilike', name), ('type', '=', 'lead' or False)]
        else:
            domain = [("name", 'ilike', name), ('type', '=', 'lead' or False), ('user_id', '=', user_id)]
        clues = request.env['crm.lead'].sudo().search(domain, limit=10, offset=0, order='id desc')
        data = []
        for clue in clues:
            data.append({
                'name': clue.name,
                'contact_name': clue.contact_name or '',
                'team': clue.team_id.display_name,
                'user': clue.user_id.display_name,
                'category': self.get_supplier_tags(clue.partner_id.category_id),
                'priority': clue.priority,
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 客户搜索
    @http.route('/linkloving_oa_api/search_customer', type='json', auth="none", csrf=False, cors='*')
    def search_customer(self, **kw):
        name = request.jsonrequest.get("name")
        type = request.jsonrequest.get("type")
        user_id = request.jsonrequest.get("user_id")
        domain = [("display_name", 'ilike', name), ('customer', '=', '1'), ('is_company', '=', True),
                  ('user_id', '=', user_id)]
        if type == 'public':  # 公海客户
            domain = [("display_name", 'ilike', name), ('customer', '=', '1'), ("is_company", '=', True),
                      ('public_partners', '=', 'public')]
        elif type == 'not_public':  # 潜在客户
            if user_id == 1:
                domain = [("display_name", 'ilike', name), ('customer', '=', '1'), ('is_company', '=', True)]
            domain.append(('public_partners', '!=', 'public'))
            domain.append(('is_order', '=', False))
        elif type == 'simple':  # 客户
            if user_id == 1:
                domain = [("display_name", 'ilike', name), ('customer', '=', '1'), ('is_company', '=', True)]
            domain.append(('is_order', '=', True))

        search_supplier_results = request.env['res.partner'].sudo().search(domain, limit=100, offset=0, order='id desc')
        json_list = []
        for feedback in search_supplier_results:
            json_list.append({
                'id': feedback.id,
                'name': feedback.display_name,
                'team': feedback.team_id.display_name,
                'user': feedback.user_id.display_name or '',
                'category': self.get_supplier_tags(feedback.category_id),
                'priority': feedback.priority,
                'level': feedback.level
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 客户（客户，潜在客户，公海客户）
    @http.route('/linkloving_oa_api/get_customers', type='json', auth="none", csrf=False, cors='*')
    def get_customers(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get("user_id")
        if user_id == 1:
            domain = [('customer', '=', '1'), ('is_company', '=', True)]
        else:
            domain = [('customer', '=', '1'), ('is_company', '=', True), ('user_id', '=', user_id)]
        if request.jsonrequest.get("is_order"):
            if request.jsonrequest.get("is_order") == 'False':  # 潜在客户
                domain.append(('is_order', '=', False))
            else:  # 客户
                domain.append(('is_order', '=', True))
        if request.jsonrequest.get("public_partners"):
            if request.jsonrequest.get("public_partners") == '!=':  # public值 !=或=
                domain.append(('public_partners', '!=', 'public'))
            else:
                domain = [('customer', '=', '1'), ('is_company', '=', True)]
                domain.append(('public_partners', '=', 'public'))

        customers = request.env['res.partner'].sudo().search(domain,
                                                             limit=limit,
                                                             offset=offset,
                                                             order='id desc')
        data = []
        for customer in customers:
            data.append({
                'name': customer.display_name,
                'team': customer.team_id.display_name,
                'user': customer.user_id.display_name or '',
                'category': self.get_supplier_tags(customer.category_id),
                'priority': customer.priority,
                'level': customer.level,
                'id': customer.id,
                'message_ids': self.message_to_json(customer.message_ids)
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 订单
    @http.route('/linkloving_oa_api/get_sale_orders', type='json', auth="none", csrf=False, cors='*')
    def get_sale_orders(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get("user_id")
        domain = []
        if request.jsonrequest.get("type"):
            type = request.jsonrequest.get("type")  # 报价单传 in  销售订单传 not in
            domain.append(('state', type, ['draft', 'sent']))
            if user_id != 1:
                domain.append(('user_id', '=', user_id))
            model = 'sale.order'
        else:
            model = 'return.goods'
            domain.append(('customer', '=', True))
        so_orders = request.env[model].sudo().search(domain,
                                                     limit=limit,
                                                     offset=offset,
                                                     order='id desc')
        # print limit,offset, user_id
        if model == 'sale.order':
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.get_so_orders_lists(so_orders))
        else:
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.get_so_orders_return_lists(so_orders))

    @classmethod
    def get_today_time_and_tz(cls):
        user = request.env["res.users"].sudo().browse(request.context.get("uid"))
        if user.tz:
            timez = fields.datetime.now(pytz.timezone(user.tz)).tzinfo._utcoffset
        else:
            timez = datetime.timedelta(seconds=8 * 3600)
        date_to_show = fields.datetime.utcnow()
        date_to_show += timez
        return date_to_show, timez

    def get_so_orders_lists(self, so_orders):
        # date_to_show, timez = LinklovingOAApi.get_today_time_and_tz()
        data = []
        for so_order in so_orders:
            data.append({
                'id': so_order.id,
                'name': so_order.name,
                # 'date_order':  time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(so_order.date_order, "%Y-%m-%d %H:%M:%S") + timez),
                'date_order': so_order.date_order,
                'validity_date': so_order.validity_date or '',
                'customer': so_order.partner_id.display_name,
                'salesman': so_order.user_id.display_name,
                'invoice_status': LinklovingOAApi.selection_get_map("sale.order", "invoice_status",
                                                                    so_order.invoice_status),
                'state': so_order.state,
                'amount_total': "%.2f" % so_order.amount_total,
                'pi_number': so_order.pi_number or '',
                'team': so_order.team_id.display_name or ''
            })
        return data

    def get_so_orders_return_lists(self, so_orders):
        data = []
        for so_order in so_orders:
            data.append({
                'id': so_order.id,
                'name': so_order.name,
                'customer': so_order.partner_id.display_name,
                'amount_total': so_order.amount_total,
                'date': so_order.date,
                'remark': so_order.remark,
                'state': LinklovingOAApi.selection_get_map("return.goods", "state", so_order.state)
            })
        return data

    # 订单详情页（报价单  销售订单）
    @http.route('/linkloving_oa_api/get_sale_orders_details', type='json', auth="none", csrf=False, cors='*')
    def get_sale_orders_details(self, *kw):
        so_id = request.jsonrequest.get("id")
        so_object = request.env['sale.order'].sudo().browse(so_id)
        data = {
            'name': so_object.name,
            'customer': so_object.partner_id.display_name,
            'state': so_object.state,
            'validity_date': so_object.validity_date or '',  # 交货日期
            'confirmation_date': so_object.confirmation_date,  # 确认日期
            'invoice_address': so_object.partner_invoice_id.display_name,  # 发票地址
            'shipping_address': so_object.partner_shipping_id.display_name,  # 送货地址
            'pricelist': so_object.pricelist_id.display_name,  # 价格表
            'payment_term': so_object.payment_term_id.display_name or '',  # 付款条款,
            'carrier': so_object.carrier_id.display_name or '',  # 交货方法
            'warehouse_id': so_object.warehouse_id.display_name,  # 仓库
            'incoterm': so_object.incoterm.display_name or '',  # 贸易术语
            'picking_policy': LinklovingOAApi.selection_get_map("sale.order", "picking_policy",
                                                                so_object.picking_policy),
            # 送货策略
            'tag_id': so_object.tag_ids.display_name or '',  # 标签
            'client_ref': so_object.client_order_ref or '',  # 客户参考
            'project_id': so_object.project_id.display_name or '',  # 分析账户
            'fiscal_position': so_object.fiscal_position_id.display_name or '',  # 财政状况
            'origin': so_object.origin or '',  # 源单据
            'campaign': so_object.campaign_id.display_name or '',
            'medium': so_object.medium_id.display_name or '',
            'source': so_object.source_id.display_name or '',
            'opportunity': so_object.opportunity_id.display_name or '',
            'team': so_object.team_id.display_name,
            'saleman': so_object.user_id.display_name,
            'remark': so_object.remark,
            'tax': so_object.tax_id.display_name,
            'pi_number': so_object.pi_number or '',
            'delivery_rule': LinklovingOAApi.selection_get_map("sale.order", "delivery_rule", so_object.delivery_rule),
            'amount_untaxed': "%.2f" % so_object.amount_untaxed,  # 未含税金额
            'amount_tax': "%.2f" % so_object.amount_tax,  # 税金
            'amount_total': "%.2f" % so_object.amount_total,  # 总计
            'order_line': self.get_so_detail_order_line(so_object.order_line)
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def get_so_detail_order_line(self, objs):
        data = []
        for obj in objs:
            data.append({
                'name': obj.product_id.display_name,
                'inner_code': obj.inner_spec or '',
                'inner_spec': obj.inner_code or '',  # 国内型号
                'uom': obj.product_uom.display_name,
                'qty': obj.product_uom_qty,  # 数量
                'price_total': "%.2f" % obj.price_total,  # 小计
                'price_unit': "%.2f" % obj.price_unit,  # 单价
                'qty_delivered': obj.qty_delivered,  # 已送货
                'qty_invoiced': obj.qty_invoiced,  # 已开票
            })
        return data

    # 订单详情页（销售退货）
    @http.route('/linkloving_oa_api/get_sale_return_details', type='json', auth="none", csrf=False, cors='*')
    def get_sale_return_details(self, *kw):
        return_so_id = request.jsonrequest.get("id")
        return_so_object = request.env['return.goods'].sudo().browse(return_so_id)
        data = {
            'name': return_so_object.name or '',
            'customer': return_so_object.partner_id.display_name or '',
            'state': LinklovingOAApi.selection_get_map("return.goods", "state", return_so_object.state),
            'invoice_address': return_so_object.partner_invoice_id.display_name or '',  # 开票地址
            'shipping_address': return_so_object.partner_shipping_id.display_name or '',  # 退货地址
            'so': return_so_object.so_id.display_name or '',  # 参考订单号
            'tracking_number': return_so_object.tracking_number or '',  # 物流信息
            'remark': return_so_object.remark or '',  # 退货原因
            'date': return_so_object.date,
            'tax': return_so_object.tax_id.display_name,
            'amount_untaxed': return_so_object.amount_untaxed,  # 未含税金额
            'amount_tax': return_so_object.amount_tax,  # 税金
            'amount_total': return_so_object.amount_total,  # 总计
            'return_line': self.get_sale_return_details_return_line(return_so_object.line_ids),
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def get_sale_return_details_return_line(self, objs):
        data = []
        for obj in objs:
            data.append({
                'product_name': obj.product_id.display_name,
                'product_uom_qty': obj.product_uom_qty,  # 退货数量
                'qty_delivered': obj.qty_delivered,  # 收到数量
                'product_uom': obj.product_uom.display_name,  # 单位
                'price_unit': obj.price_unit,  # 单价
                'price_subtotal': obj.price_subtotal,  # 小计
                'qty_to_invoice': obj.qty_to_invoice,  # 待对账数量
                'invoice_status': LinklovingOAApi.selection_get_map("return.goods", "invoice_status",
                                                                    obj.invoice_status)
                # 对账状态
            })
        return data

    # 销售订单搜索
    @http.route('/linkloving_oa_api/search_sale_orders', type='json', auth="none", csrf=False, cors='*')
    def search_sale_orders(self, *kw):
        name = request.jsonrequest.get("name")
        model = request.jsonrequest.get("model")
        state = request.jsonrequest.get("state")
        user_id = request.jsonrequest.get("user_id")
        if model == 'sale.order':
            if state == 'draft':
                domain = [('state', 'in', ('draft', 'sent')), ('name', 'ilike', name)]
            elif state == 'purchase':
                domain = [('state', 'not in', ('draft', 'sent')), ('name', 'ilike', name)]
        elif model == 'return.goods':
            domain = [('customer', '=', True), ('name', 'ilike', name)]
        if user_id != 1:
            domain.append(('user_id', '=', user_id))
        sale_orders = request.env[model].sudo().search(domain, limit=10, offset=0, order='id desc')
        if model == 'sale.order':
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.get_so_orders_lists(sale_orders))
        else:
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.get_so_orders_return_lists(sale_orders))

    # 创建报价单页的小接口
    @http.route('/linkloving_oa_api/get_all_customers', type='json', auth="none", csrf=False, cors='*')
    def get_all_customers(self, *kw):
        if request.jsonrequest.get("type") == 'customers':  # 返回所有客户名
            limit = request.jsonrequest.get("limit")
            offset = request.jsonrequest.get("offset")
            domain = [('customer', '=', 1), ('is_company', '=', True), ('is_order', '=', True)]
            customers = request.env["res.partner"].sudo().search(domain,
                                                                 limit=limit,
                                                                 offset=offset,
                                                                 order='id desc')
            return self.get_name_and_id(customers)
        elif request.jsonrequest.get("type") == 'delivery':  # 交货规则
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=self.selection_get("sale.order", "delivery_rule"))
        elif request.jsonrequest.get("type") == 'tax':  # 税金
            field_details = request.env['account.tax'].sudo().search([])
            return self.get_name_and_id(field_details)
        elif request.jsonrequest.get("type") == 'pricelist':  # 价格表
            pricelists = request.env['product.pricelist'].sudo().search([])
            return self.get_name_and_id(pricelists)
        elif request.jsonrequest.get("type") == 'payment_term':  # 付款条款
            payment_terms = request.env['account.payment.term'].sudo().search([])
            return self.get_name_and_id(payment_terms)
        elif request.jsonrequest.get("type") == 'delivery_way':  # 交货方法
            delivery_ways = request.env['delivery.carrier'].sudo().search([])
            return self.get_name_and_id(delivery_ways)
        elif request.jsonrequest.get("type") == 'warehouse':  # 获取仓库
            warehouses = request.env['stock.warehouse'].sudo().search([])
            return self.get_name_and_id(warehouses)
        elif request.jsonrequest.get("type") == 'picking_policy':  # 送货策略
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=self.selection_get("sale.order", "picking_policy"))
        elif request.jsonrequest.get("type") == 'team':  # 销售团队
            teams = request.env['crm.team'].sudo().search([])
            return self.get_name_and_id(teams)
        elif request.jsonrequest.get("type") == 'analytic_account':  # 分析账户
            analytic_accounts = request.env['account.analytic.account'].sudo().search([])
            return self.get_name_and_id(analytic_accounts)
        elif request.jsonrequest.get("type") == 'incoterm':  # 贸易术语
            incoterms = request.env['stock.incoterms'].sudo().search([])
            return self.get_name_and_id(incoterms)
        elif request.jsonrequest.get("type") == 'tags':  # 标签
            tags = request.env['crm.lead.tag'].sudo().search([])
            return self.get_name_and_id(tags)
        elif request.jsonrequest.get("type") == 'fiscal':  # 财政状况
            fiscal = request.env['account.fiscal.position'].sudo().search([])
            return self.get_name_and_id(fiscal)

    # 获取name和id
    def get_name_and_id(self, objs):
        data = []
        for obj in objs:
            data.append({
                'name': obj.display_name,
                'id': obj.id
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 取消订单的接口
    @http.route('/linkloving_oa_api/cancel_order', type='json', auth="none", csrf=False, cors='*')
    def cancel_order(self, *kw):
        order_id = request.jsonrequest.get("id")
        cancel_order = request.env["sale.order"].sudo().browse(order_id)
        cancel_order.action_cancel()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 确认销售的接口
    @http.route('/linkloving_oa_api/confirm_order', type='json', auth="none", csrf=False, cors='*')
    def order_confirm(self, *kw):
        order_id = request.jsonrequest.get("id")
        confirm_order = request.env["sale.order"].sudo().browse(order_id)
        confirm_order.action_confirm()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 切换公司
    @http.route('/linkloving_oa_api/change_company', type='json', auth="none", csrf=False, cors='*')
    def change_company(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        user = request.env["res.users"].sudo().browse(user_id)
        if request.jsonrequest.get("id"):
            choose_id = request.jsonrequest.get("id")
            user = request.env["res.users"].sudo().browse(user_id)
            user.company_id = choose_id
            return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})
        else:
            companies = user.company_ids
            data = []
            for company in companies:
                data.append({
                    'id': company.id,
                    'name': company.name
                })
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取产品
    @http.route('/linkloving_oa_api/get_products', type='json', auth="none", csrf=False, cors='*')
    def get_products(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        if request.jsonrequest.get("name"):
            name = request.jsonrequest.get("name")
            products = request.env['product.product'].sudo().search(
                ['|', ('name', 'ilike', name), ('default_code', 'ilike', name), ('sale_ok', '=', True)], limit=10,
                offset=0, order='id asc')
        else:
            products = request.env['product.product'].sudo().search([('sale_ok', '=', True)],
                                                                    limit=limit,
                                                                    offset=offset,
                                                                    order='id desc')
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.get_product_detail(products))

    def get_product_detail(self, objs):
        data = []
        for product in objs:
            data.append({
                'name': product.name,
                'id': product.id,
                'inner_code': product.inner_code or '',  # 国内简称
                'inner_spec': product.inner_spec or '',  # 国内型号
                'categ_id': product.categ_id.display_name,  # 内部类别
                'default_code': product.default_code,  # 内部参考
                'uom': product.uom_id.display_name,
                'uom_id': product.uom_id.id,
                'virtual_qty': product.virtual_available,
                'qty_available': product.qty_available
            })
        return data

    # 根据料号搜索产品
    @http.route('/linkloving_oa_api/search_products_by_material_no', type='json', auth="none", csrf=False, cors='*')
    def search_products_by_material_no(self, *kw):
        name = request.jsonrequest.get("name")
        products = request.env['product.product'].sudo().search([('default_code', '=', name)], limit=1, offset=0,
                                                                order='id asc')
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.get_product_detail(products))

    # 根据客户选择发票、送货地址
    @http.route('/linkloving_oa_api/choose_customer', type='json', auth="none", csrf=False, cors='*')
    def choose_customer(self, *kw):
        partner_id = request.jsonrequest.get("id")
        type = request.jsonrequest.get("type")  # type=delivery获取送货地址  type=invoice获取发票地址
        partners = request.env['res.partner'].sudo().search([('parent_id', '=', partner_id), ('type', '=', type)],
                                                            limit=10, offset=0, order='id desc')
        data = []
        for partner in partners:
            data.append({
                'address': partner.display_name,
                'id': partner.id
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 创建报价单
    @http.route('/linkloving_oa_api/create_so_order_draft', type='json', auth="none", csrf=False, cors='*')
    def create_so_order_draft(self, *kw):
        data = request.jsonrequest.get("data")
        print data.get('productions')
        new_order_draft = request.env["sale.order"].sudo().create({
            'partner_id': data.get('cusomer'),
            'partner_invoice_id': data.get('improveQuotation').get('invoiceAddress'),
            'partner_shipping_id': data.get('improveQuotation').get('deliveryAddress'),
            'tax_id': data.get('tax'),
            'validity_date': data.get('deliveryDate'),
            'delivery_rule': data.get('delivery') or '',
            'pi_number': data.get('improveQuotation').get('PINumber') or '',
            'warehouse_id': data.get('improveQuotation').get('deliveryInfo').get('warehouse'),
            'picking_policy': data.get('improveQuotation').get('deliveryInfo').get('picking_policy'),
            'team_id': data.get('improveQuotation').get('salesInfo').get('team') or '',
            'user_id': data.get('improveQuotation').get('salesInfo').get('salesMan'),
            'order_line': [(0, 0, {
                'product_id': p.get('id'),
                'product_uom_qty': float(p.get('orderNumber')),
                'price_unit': float(p.get('orderPrice')),
                'product_uom': p.get('uom_id'),
                'tax_id': [(6, 0, [int(data.get('tax'))])]
            }) for p in data.get('productions')]
        })
        print 'aaaaaaaa'
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 取消订单的接口
    @http.route('/linkloving_oa_api/cancel_order', type='json', auth="none", csrf=False, cors='*')
    def cancel_order(self, *kw):
        order_id = request.jsonrequest.get("id")
        cancel_order = request.env["sale.order"].sudo().browse(order_id)
        cancel_order.action_cancel()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 转为报价单接口
    @http.route('/linkloving_oa_api/to_draft', type='json', auth="none", csrf=False, cors='*')
    def to_draft(self, *kw):
        order_id = request.jsonrequest.get("id")
        cancel_order = request.env["sale.order"].sudo().browse(order_id)
        cancel_order.action_draft()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 确认销售的接口
    @http.route('/linkloving_oa_api/confirm_order', type='json', auth="none", csrf=False, cors='*')
    def order_confirm(self, *kw):
        order_id = request.jsonrequest.get("id")
        confirm_order = request.env["sale.order"].sudo().browse(order_id)
        confirm_order.action_confirm()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 客户详情页
    @http.route('/linkloving_oa_api/customer_details', type='json', auth="none", csrf=False, cors='*')
    def customer_details(self, *kw):
        id = request.jsonrequest.get("id")
        customer = request.env["res.partner"].sudo().browse(id)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.get_customer_details(customer))

    def get_customer_details(self, obj):
        data = {
            'id': obj.id,
            'country': obj.country_id.display_name or '',
            'name': obj.display_name,
            'address': (obj.country_id.display_name or '') + (obj.state_id.name or '') + (obj.city or '') + (
                obj.street2 or '') + (obj.street or ''),
            'phone': obj.phone or '',
            'crm_source': obj.crm_source_id.display_name or '',  # 来源
            'source': obj.source_id.display_name or '',  # 渠道
            'team': obj.team_id.display_name or '',
            'user_id': obj.user_id.display_name or '',
            'tag': self.get_supplier_tags(obj.category_id),
            'priority': obj.priority,
            'level': obj.level or '',
            "contracts_count": len(obj.child_ids),  # 联系人&地址个数
            "contracts": self.get_contracts_in_supplier(obj.child_ids),
            # 'supplier': obj.supplier_invoice_count,  #对账数量
            'supplier': request.env['account.invoice'].sudo().search_count(
                [('partner_id', '=', request.jsonrequest.get("id"))]),
            # 'purchase_count': obj.purchase_order_count,    #订单数量
            'purchase_count': request.env['sale.order'].sudo().search_count(
                [('partner_id', '=', request.jsonrequest.get("id"))]),
            'return_count': request.env['stock.picking'].sudo().search_count(
                [('partner_id', '=', request.jsonrequest.get("id")), ('state', '=', 'waiting_in')]),
            # 退货入库数量
            'product_series': self.get_series_products(obj.product_series_ids),
            'message_ids': self.message_to_json(obj.message_ids),
        }
        return data

    def get_series_products(self, objs):
        data = []
        for obj in objs:
            data.append({
                'name': obj.display_name,
                'crm_product_type': LinklovingOAApi.selection_get_map("crm.product.series", "crm_product_type",
                                                                      obj.crm_product_type),
                'detail': obj.detail or '',
                'parent': obj.crm_Parent_id.display_name,
                'ontomany': self.get_on_to_many(obj.crm_Parent_ontomany_ids)
            })
        return data

    def get_on_to_many(self, objs):
        data = []
        for obj in objs:
            data.append({
                'name': obj.display_name
            })
        return data

    # 产品详情页
    @http.route('/linkloving_oa_api/product_details', type='json', auth="none", csrf=False, cors='*')
    def product_details(self, *kw):
        if request.jsonrequest.get("code"):
            product = \
                request.env["product.template"].sudo().search([('default_code', '=', request.jsonrequest.get("code"))])[
                    0]
        else:
            id = request.jsonrequest.get("id")
            product = request.env["product.product"].sudo().browse(id).product_tmpl_id
        data = {
            'qty_available': product.qty_available,  # 库存
            'qty_virtual': product.virtual_available,  # 预测
            'code': product.default_code,  # 料号
            'name': product.name,
            'area': product.area_id.display_name or '',
            'inner_code': product.inner_code or '',
            'inner_spec': product.inner_spec or '',
            'product_specs': product.product_specs or '',  # 产品规格
            'categ_id': product.categ_id.display_name,  # 内部类别
            'stock_move': self.get_product_stock_move(product.product_variant_ids[0].id),
            'image': LinklovingOAApi.get_img_url(product.id, "product.template", "image"),
            'bom': self.get_boms(product)
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def get_product_stock_move(self, id):
        data = []
        # for id in ids:
        objs = request.env["stock.move"].sudo().search([('product_id', '=', id)])
        for obj in objs:
            data.append({
                'name': obj.name,
                'product_uom_qty': obj.product_uom_qty,
                'location': obj.location_id.display_name,  # 来源位置
                'location_dest': obj.location_dest_id.display_name  # 目的位置
            })
        return data

    @classmethod
    def get_img_url(cls, id, model, field):
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s&time=%s' % (
            request.httprequest.host_url, str(id), model, field, str(time.mktime(datetime.datetime.now().timetuple())))
        if not url:
            return ''
        return url

    def get_boms(self, product):
        if product.bom_ids:
            return product.bom_ids.get_bom()
        else:
            return ''

    def res_user_to_json(self, objs):
        data = []
        for obj in objs:
            data.append({
                'user_id': obj.id,
                'name': obj.name,
            })
        return data

    # 去掉<p>标签
    def message_to_json(self, objs):
        data = []
        for obj in objs:
            dr = re.compile(r'<[^>]+>', re.S)
            body_str = dr.sub('', obj.body)
            # body_str = body_str.replace('</p>', '')
            data.append({
                'model': obj.model,
                'body': body_str,
                'email_from': obj.email_from,
                'date': obj.date,
                'create_uid': self.res_user_to_json(obj.create_uid)
            })
        return data

    @http.route('/linkloving_oa_api/create_info', type='json', auth="none", csrf=False, cors='*')
    def create_info(self, *kw):
        body = request.jsonrequest.get("body")
        author_id = request.jsonrequest.get("author_id")
        message_label_ids = request.jsonrequest.get("message_label_ids")
        res_id = request.jsonrequest.get("res_id")
        create_uid = request.jsonrequest.get("create_uid")
        # data = {
        #     'body':body,
        #     'message_type':'comment',
        #     'model':'res.partner',
        #     'res_id':res_id,
        #     'subtype_id':1,
        #     'messages_label_ids':message_label_ids,
        #     'author_id':author_id,
        # }
        # domain = [("id", '=', res_id)]
        new_partner_info = request.env["mail.message"].sudo(create_uid).create({
            'body': body,
            'message_type': 'comment',
            'model': 'res.partner',
            'res_id': res_id,
            'subtype_id': 1,
            'messages_label_ids': message_label_ids,
            'author_id': author_id,
            'create_uid': create_uid,
        })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    @http.route('/linkloving_oa_api/get_all_message_label', type='json', auth="none", csrf=False, cors='*')
    def get_all_message_label(self, *kw):
        get_all_messages = request.env["message.label"].sudo().search([])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.message_label_to_json(get_all_messages))

    def message_label_to_json(self, objs):
        data = []
        for obj in objs:
            data.append({
                'id': obj.id,
                'name': obj.name,
            })
        return data

    # 报销-等待审核
    @http.route('/linkloving_oa_api/wait_approval', type='json', auth="none", csrf=False, cors='*')
    def product_details(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get("user_id")
        domain = [("to_approve_id", '=', user_id),
                  ('state', 'in', ('submit', 'manager1_approve', 'manager2_approve'))]
        approval_lists = request.env["hr.expense.sheet"].sudo().search(domain,
                                                                       limit=limit,
                                                                       offset=offset,
                                                                       order='id desc')
        json_list = []
        for approval_list in approval_lists:
            json_list.append(self.approval_list_to_json(approval_list))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    def approval_list_to_json(self, obj):
        return {
            'sheet_id': obj.id,
            'expense_name': obj.expense_no or '',
            'employee_name': obj.employee_id.name or '',
            'amount': obj.total_amount or '',
            'create_date': obj.create_date or '',
            'department': obj.department_id.name or '',
            'remark': obj.name or '',
            'state': obj.state or '',
            'pre_payment_reminding': obj.pre_payment_reminding or '0.00',
            'line_ids': self.get_waiting_approval_detail_lists(obj.expense_line_ids),
            'message_ids': self.get_apply_record(obj.message_ids),
            'to_approve_id': obj.to_approve_id.id,
        }

    def get_waiting_approval_detail_lists(self, objs):
        data = []
        for obj in objs:
            data.append({
                'line_id': obj.id,
                'analytic_account_id': obj.analytic_account_id.name or '',
                'product_id': obj.product_id.name or '',
                'account_id': obj.account_id.name or '',
                'unit_amount': obj.unit_amount or '',
                # 'sale_id':obj.sale_id,
                'quantity': obj.quantity or '',
                'tax_ids': self.get_tax_ids_to_json(obj.tax_ids),
                'name': obj.name or '',
                'description': obj.description or '',
            })
        return data

    def get_tax_ids_to_json(self, objs):
        data = []
        for obj in objs:
            data.append({
                'display_name': obj.display_name or '',
            })
        return data

    # 报销-已审核
    @http.route('/linkloving_oa_api/already_approved', type='json', auth="none", csrf=False, cors='*')
    def already_approved(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get("user_id")
        domain = [("approve_ids", "child_of", user_id)]
        already_approved = request.env["hr.expense.sheet"].sudo().search(domain,
                                                                         limit=limit,
                                                                         offset=offset,
                                                                         order='id desc')
        json_list = []
        for approval_list in already_approved:
            json_list.append(self.approval_list_to_json(approval_list))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list[0:10])

    # 批准 发送状态的
    @http.route('/linkloving_oa_api/confirm_approve1', type='json', auth="none", csrf=False, cors='*')
    def confirm_approve1(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        domain = [("id", '=', sheet_id)]
        reason = request.jsonrequest.get("reason")
        expense_line_ids = request.jsonrequest.get("expense_line_ids")
        confirm_approve = request.env["hr.expense.sheet"].sudo(user_id).search(domain)
        for line_ids in confirm_approve.expense_line_ids:
            for request_line in expense_line_ids.get('data').get('expense_line_ids'):
                if (line_ids.id == request_line.get('line_id')):
                    line_ids.write({
                        'product_id': request_line.get('product_id'),  # 产品
                        'unit_amount': float(request_line.get('unit_amount')),  # 金额
                        'name': request_line.get('name'),  # 费用说明
                        'tax_ids': (
                            [(6, 0, [request_line.get('taxid')])] if type(request_line.get('taxid')) == int else [
                                (6, 0, [4])]),
                        'description': request_line.get('remarks'),
                    })

        confirm_approve.manager1_approve()
        if reason:
            confirm_approve.create_message_post(reason)

        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 批准 1级审核的
    @http.route('/linkloving_oa_api/confirm_approve2', type='json', auth="none", csrf=False, cors='*')
    def confirm_approve(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        domain = [("id", '=', sheet_id)]
        reason = request.jsonrequest.get("reason")
        expense_line_ids = request.jsonrequest.get("expense_line_ids")
        confirm_approve = request.env["hr.expense.sheet"].sudo(user_id).search(domain)

        for line_ids in confirm_approve.expense_line_ids:
            for request_line in expense_line_ids.get('data').get('expense_line_ids'):
                if (line_ids.id == request_line.get('line_id')):
                    line_ids.write({
                        'product_id': request_line.get('product_id'),  # 产品
                        'unit_amount': float(request_line.get('unit_amount')),  # 金额
                        'name': request_line.get('name'),  # 费用说明
                        'tax_ids': (
                            [(6, 0, [request_line.get('taxid')])] if type(request_line.get('taxid')) == int else [
                                (6, 0, [4])]),
                        'description': request_line.get('remarks'),
                    })

        confirm_approve.manager2_approve()
        if reason:
            confirm_approve.create_message_post(reason)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 修改 2级审核
    @http.route('/linkloving_oa_api/confirm_approve3', type='json', auth="none", csrf=False, cors='*')
    def confirm_approve3(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        domain = [("id", '=', sheet_id)]
        reason = request.jsonrequest.get("reason")
        confirm_approve = request.env["hr.expense.sheet"].sudo(user_id).search(domain)
        expense_line_ids = request.jsonrequest.get("expense_line_ids")

        for line_ids in confirm_approve.expense_line_ids:
            for request_line in expense_line_ids.get('data').get('expense_line_ids'):
                if (line_ids.id == request_line.get('line_id')):
                    line_ids.write({
                        'product_id': request_line.get('product_id'),  # 产品
                        'unit_amount': float(request_line.get('unit_amount')),  # 金额
                        'name': request_line.get('name'),  # 费用说明
                        'tax_ids': (
                            [(6, 0, [request_line.get('taxid')])] if type(request_line.get('taxid')) == int else [
                                (6, 0, [4])]),
                        'description': request_line.get('remarks'),
                    })

        confirm_approve.manager3_approve()
        if reason:
            confirm_approve.create_message_post(reason)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 拒绝
    @http.route('/linkloving_oa_api/refuse_approve', type='json', auth="none", csrf=False, cors='*')
    def refuse_approve(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        refuse_reason = request.jsonrequest.get("reason")
        domain = [("id", '=', sheet_id)]
        refuse_approve = request.env["hr.expense.sheet"].sudo(user_id).search(domain)
        refuse_approve.refuse_expenses(refuse_reason)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 搜索报销单
    @http.route('/linkloving_oa_api/search_approve', type='json', auth="none", csrf=False, cors='*')
    def search_approve(self, *kw):
        type = request.jsonrequest.get("type")
        search_text = request.jsonrequest.get("search_text")
        user_id = request.jsonrequest.get("user_id")
        if (type == 'expense_no'):
            domain = [("to_approve_id", '=', user_id),
                      ('state', 'in', ('submit', 'manager1_approve', 'manager2_approve')),
                      (type, 'ilike', search_text)]
            search_approve = request.env["hr.expense.sheet"].sudo().search(domain,
                                                                           order='id desc')
            json_list = []
            for search_approval_list in search_approve:
                json_list.append(self.approval_list_to_json(search_approval_list))
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)
        elif (type == 'name'):
            domain = [("to_approve_id", '=', user_id),
                      ('state', 'in', ('submit', 'manager1_approve', 'manager2_approve')),
                      ]
            search_approve = request.env["hr.expense.sheet"].sudo().search(domain,
                                                                           order='id desc')
            json_list = []
            for search_approval_list in search_approve:
                if (search_approval_list.employee_id.name.find(search_text) != -1):
                    json_list.append(self.approval_list_to_json(search_approval_list))
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 搜索已审的
    @http.route('/linkloving_oa_api/search_already_approve', type='json', auth="none", csrf=False, cors='*')
    def search_already_approve(self, *kw):
        type = request.jsonrequest.get("type")
        search_text = request.jsonrequest.get("search_text")
        user_id = request.jsonrequest.get("user_id")
        if (type == 'expense_no'):
            domain = [("approve_ids", "child_of", user_id), (type, 'ilike', search_text)]
            search_already_approved = request.env["hr.expense.sheet"].sudo().search(domain,
                                                                                    order='id desc')
            json_list = []
            for approval_list in search_already_approved:
                json_list.append(self.approval_list_to_json(approval_list))
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)
        elif (type == 'name'):
            domain = [("approve_ids", "child_of", user_id), ("employee_id", "ilike", search_text)]
            search_already_approved = request.env["hr.expense.sheet"].sudo().search(domain,
                                                                                    order='id desc')
            json_list = []
            for approval_list_name in search_already_approved:
                json_list.append(self.approval_list_to_json(approval_list_name))
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 我的申购
    @http.route('/linkloving_oa_api/get_shengoulist', type='json', auth="none", csrf=False, cors='*')
    def get_shengoulist(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get('user_id')
        domain = [('create_uid', '=', user_id)]
        shengoulist = request.env['hr.purchase.apply'].sudo().search(domain,
                                                                     limit=limit,
                                                                     offset=offset,
                                                                     order='id desc')
        data = []
        for shengou in shengoulist:
            data.append(self.shengou_list_to_json(shengou))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

        # 拒绝

    @http.route('/linkloving_oa_api/refuse_shengou', type='json', auth="none", csrf=False, cors='*')
    def refuse_shengou(self, *kw):
        sheet_id = request.jsonrequest.get('sheet_id')
        user_id = request.jsonrequest.get('user_id')
        refuse_reason = request.jsonrequest.get('reason')
        domain = [('id', '=', sheet_id)]
        shengou = request.env['hr.purchase.apply'].sudo(user_id).search(domain,
                                                                        order='id desc')
        shengou.refuse_payment(refuse_reason);
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 重新申请
    @http.route('/linkloving_oa_api/reset_shengou', type='json', auth="none", csrf=False, cors='*')
    def reset_shengou(self, *kw):
        sheet_id = request.jsonrequest.get('sheet_id')
        user_id = request.jsonrequest.get('user_id')
        data = request.jsonrequest.get('line_data')
        department_id = request.jsonrequest.get('department_id')
        domain = [('id', '=', sheet_id)]
        reset_shengou = request.env['hr.purchase.apply'].sudo(user_id).search(domain,
                                                                              order='id desc')

        reset_shengou.write({
            'department_id': department_id,
        })
        shengou_lines = reset_shengou.line_ids
        for shengou_line in shengou_lines:
            request.env['hr.purchase.apply.line'].sudo().browse(shengou_line.id).unlink()

        for p in data.get('data').get('line_ids'):
            request.env['hr.purchase.apply.line'].sudo().create({
                'product_id': p.get('product_id'),  # 产品
                'product_qty': float(p.get('quantity')),
                'price_unit': float(p.get('price_unit')),
                'description': p.get('description'),
                'apply_id': reset_shengou.id,
            })

        reset_shengou.reset_hr_purchase_apply();
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 获取所有部门
    @http.route('/linkloving_oa_api/get_all_departments', type='json', auth="none", csrf=False, cors='*')
    def get_all_departments(self, *kw):
        partner_id = request.jsonrequest.get('partner_id')
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', partner_id)])
        get_all_departments = request.env['hr.department'].sudo().search([])
        # domain = [('address_home_id', '=', partner_id)]
        # person_department = request.env['hr.employee'].sudo().search(domain,
        # order='id desc')
        data = {
            "all_departments": self.get_department_to_json(get_all_departments),
            "default_department": self.get_name_and_id(employee.department_id),
            "employee_id": employee.id,
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取所有产品
    @http.route('/linkloving_oa_api/get_all_products', type='json', auth="none", csrf=False, cors='*')
    def get_all_products(self, *kw):
        get_all_products = request.env['product.product'].sudo().search(
            [('can_be_expensed', '=', True)])
        data = self.get_name_and_id(get_all_products)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 创建申购单
    @http.route('/linkloving_oa_api/create_shengou', type='json', auth="none", csrf=False, cors='*')
    def create_shengou(self, *kw):
        data = request.jsonrequest.get("data")
        create_uid = data.get('create_uid')
        new_shengou = request.env['hr.purchase.apply'].sudo(create_uid).create({
            'department_id': data.get('department_id'),  # 部门
            'employee_id': data.get('employee_id'),  # 申请人
            'total_amount': float(data.get('total_amount')),
            'create_uid': data.get('create_uid'),
            'line_ids': [(0, 0, {
                'product_id': p.get('product_id'),  # 产品
                'price_unit': float(p.get('price_unit')),  # 金额
                'product_qty': float(p.get('quantity')),  # 费用说明
                'description': p.get('description'),
            }) for p in data.get('line_ids')]
        })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.shengou_list_to_json(new_shengou))

    # 提交申请
    @http.route('/linkloving_oa_api/push_apply', type='json', auth="none", csrf=False, cors='*')
    def push_apply(self, *kw):
        sheet_id = request.jsonrequest.get('sheet_id')
        user_id = request.jsonrequest.get('user_id')
        domain = [('id', '=', sheet_id)]
        shengou = request.env['hr.purchase.apply'].sudo(user_id).search(domain,
                                                                        order='id desc')
        shengou.hr_purchase_apply_post()
        JPushExtend.send_notification_push(audience=jpush.audience(
            jpush.alias(shengou.to_approve_id.id)
        ), notification=shengou.name,
            body=_("申购单：%s 等待审核！") % (shengou.name))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 搜索申购单
    @http.route('/linkloving_oa_api/search_shengou', type='json', auth="none", csrf=False, cors='*')
    def search_shengou(self, *kw):
        search_text = request.jsonrequest.get('search_text')
        user_id = request.jsonrequest.get('user_id')
        domain = [('create_uid', '=', user_id), ('name', 'ilike', search_text)]
        shengoulist = request.env['hr.purchase.apply'].sudo().search(domain,
                                                                     order='id desc')
        data = []
        for shengou in shengoulist:
            data.append(self.shengou_list_to_json(shengou))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def get_department_to_json(self, obj):
        data = []
        for objs in obj:
            data.append({
                'name': objs.display_name,
                'id': objs.id
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def shengou_list_to_json(self, obj):
        return {
            'sheet_id': obj.id,
            'name': obj.name or '',
            'employee_name': obj.employee_id.name or '',
            'total_amount': obj.total_amount or '',
            'create_date': obj.create_date or '',
            'department': self.get_department(obj.department_id),
            'state': obj.state or '',
            'line_ids': self.get_shengou_detail_lists(obj.line_ids),
            'message_ids': self.get_apply_record(obj.message_ids),
        }

    def get_shengou_detail_lists(self, obj):
        data = []
        for obj_d in obj:
            data.append({
                # 'analytic_account_id': obj_d.analytic_account_id.name or '',
                'product_id': self.get_department(obj_d.product_id),
                'quantity': obj_d.product_qty,
                'description': obj_d.description or '',
                'price_unit': obj_d.price_unit or 0.0,
            })
        return data

    def get_department(self, objs):
        return {
            'name': objs.name or '',
            'id': objs.id or '',
        }

    # 联系人
    @http.route('/linkloving_oa_api/get_departments', type='json', auth="none", csrf=False, cors='*')
    def get_departments(self, *kw):
        departments = request.env['hr.department'].sudo().search([], order='id asc')
        data = []
        for department in departments:
            data.append(self.change_department_to_json(department))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取所有联系人
    @http.route('/linkloving_oa_api/get_all_employees', type='json', auth="none", csrf=False, cors='*')
    def get_all_employees(self, *kw):
        employees = request.env['hr.employee'].sudo().search([], order='id asc')
        data = []
        for employee in employees:
            data.append(self.change_employee_to_json(employee))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def change_employee_to_json(self, obj_d):
        return {
            'name': obj_d.name_related,  # 姓名
            'work_phone': obj_d.work_phone or '',  # 办公电话
            'mobile_phone': obj_d.mobile_phone or '',  # 办公手机
            'work_email': obj_d.work_email or '',  # email
            'department_id': self.get_department(obj_d.department_id),  # 部门
            'job_id': self.get_department(obj_d.job_id),  # 工作头衔
            'parent_id': self.get_department(obj_d.parent_id),  # 经理
            'image': self.get_img_url(obj_d.id, "hr.employee", "image_medium",
                                      obj_d.write_date.replace("-", "").replace(" ", "").replace(":", "")),
            # 头像
        }

    def change_department_to_json(self, objs):
        return {
            'total_employee': objs.total_employee,
            'name': objs.name,
            'id': objs.id,
        }

    # 部门详情
    @http.route('/linkloving_oa_api/get_department_detail', type='json', auth="none", csrf=False, cors='*')
    def get_department_detail(self, *kw):
        department_id = request.jsonrequest.get('department_id')
        department_detail = request.env['hr.employee'].sudo().search([('department_id', '=', department_id)],
                                                                     order='id desc')
        data = []
        for department in department_detail:
            data.append(self.change_department_detail_to_json(department))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def change_department_detail_to_json(self, objs):
        data = []
        for obj_d in objs:
            data.append({
                'name': obj_d.name_related,  # 姓名
                'work_phone': obj_d.work_phone or '',  # 办公电话
                'mobile_phone': obj_d.mobile_phone or '',  # 办公手机
                'work_email': obj_d.work_email or '',  # email
                'department_id': self.get_department(obj_d.department_id),  # 部门
                'job_id': self.get_department(obj_d.job_id),  # 工作头衔
                'parent_id': self.get_department(obj_d.parent_id),  # 经理
                'image': self.get_img_url(obj_d.id, "hr.employee", "image_medium",
                                          obj_d.write_date.replace("-", "").replace(" ", "").replace(":", "")),
                # 头像
            })
        return data

    # 头像json
    def get_img_url(cls, id, model, field, time):
        url = '%sweb/image?model=%s&id=%s&field=%s&unique=%s' % (
            request.httprequest.host_url, model, str(id), field, time)
        if not url:
            return ''
        return url

    # 我的工程领料单
    @http.route('/linkloving_oa_api/get_material_request_list', type='json', auth="none", csrf=False, cors='*')
    def get_material_request_list(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get('user_id')
        material_request_list = request.env['material.request'].sudo().search([('create_uid', '=', user_id)],
                                                                              limit=limit,
                                                                              offset=offset,
                                                                              order='id desc')
        data = []
        for material_request in material_request_list:
            data.append({
                "name": material_request.name,
                "picking_type": material_request.picking_type,
                "my_create_uid": self.get_department(material_request.my_create_uid),
                "delivery_date": material_request.delivery_date,
                "my_create_date": material_request.my_create_date,
                "picking_state": material_request.picking_state,
                "who_review_now": self.get_department(material_request.who_review_now),
                "picking_cause": material_request.picking_cause,
                "remark": material_request.remark or '无',
                "line_ids": self.change_material_request_line_ids_to_json((material_request.line_ids)),
                "user_ava": LinklovingAppApi.get_img_url(material_request.create_uid.id,
                                                         "res.users", "image_medium"),
                "review_process_line_ids": self.change_shenpi_line_ids_tojson(material_request.review_process_line_ids)

            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 工程领料 待我审批
    @http.route('/linkloving_oa_api/get_wait_me_material_request_list', type='json', auth="none", csrf=False, cors='*')
    def get_wait_me_material_request_list(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get('user_id')
        wait_me_material_request_list = request.env['material.request'].sudo().search(
            [('who_review_now_id', '=', user_id), ("picking_state", "=", "review_ing")],
            limit=limit,
            offset=offset,
            order='id desc')
        total_material_request_list = request.env['material.request'].sudo().search(
            [('who_review_now_id', '=', user_id), ("picking_state", "=", "review_ing")],
            order='id desc')
        data = []
        count = 0;
        for list in total_material_request_list:
            count = count + 1

        for material_request in wait_me_material_request_list:
            data.append({
                "id": material_request.id,
                "name": material_request.name,
                "picking_type": material_request.picking_type,
                "my_create_uid": self.get_department(material_request.my_create_uid),
                "delivery_date": material_request.delivery_date,
                "my_create_date": material_request.my_create_date,
                "picking_state": material_request.picking_state,
                "who_review_now": self.get_department(material_request.who_review_now),
                "picking_cause": material_request.picking_cause,
                "remark": material_request.remark or '无',
                "line_ids": self.change_material_request_line_ids_to_json((material_request.line_ids)),
                "user_ava": LinklovingAppApi.get_img_url(material_request.create_uid.id,
                                                         "res.users", "image_medium"),
                "review_process_line_ids": self.change_shenpi_line_ids_tojson(material_request.review_process_line_ids),

            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"data": data, "count": count})

    # 工程领料 我已审批
    @http.route('/linkloving_oa_api/get_already_material_request_list', type='json', auth="none", csrf=False, cors='*')
    def get_already_material_request_list(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get('user_id')
        already_material_requset = request.env['material.request'].sudo().search(
            [("review_i_approvaled_val", "child_of", user_id)],
            limit=limit,
            offset=offset,
            order='id desc'
        )
        data = []
        for material_request in already_material_requset:
            data.append({
                "name": material_request.name,
                "picking_type": material_request.picking_type,
                "my_create_uid": self.get_department(material_request.my_create_uid),
                "delivery_date": material_request.delivery_date,
                "my_create_date": material_request.my_create_date,
                "picking_state": material_request.picking_state,
                "who_review_now": self.get_department(material_request.who_review_now),
                "picking_cause": material_request.picking_cause,
                "remark": material_request.remark or '无',
                "line_ids": self.change_material_request_line_ids_to_json((material_request.line_ids)),
                "user_ava": LinklovingAppApi.get_img_url(material_request.create_uid.id,
                                                         "res.users", "image_medium"),
                "review_process_line_ids": self.change_shenpi_line_ids_tojson(material_request.review_process_line_ids)
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取终审人
    @http.route('/linkloving_oa_api/get_final_review', type='json', auth="none", csrf=False, cors='*')
    def get_final_review(self, *kw):
        final_review_list = request.env['final.review.partner'].sudo().search([])
        data = []
        for final_review in final_review_list:
            data.append({
                "final_review_partner_id": self.get_department(final_review.final_review_partner_id),
                "review_type": final_review.review_type,
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 搜索审核人
    @http.route('/linkloving_oa_api/search_employee', type='json', auth="none", csrf=False, cors='*')
    def search_employee(self, *kw):
        name = request.jsonrequest.get("name")
        search_employee = request.env['res.partner'].sudo().search([('name', 'ilike', name), ('employee', '=', 't')])
        data = []
        for employee in search_employee:
            data.append({
                "partner_id": {
                    "name": employee.name,
                    "id": employee.id,
                },
                # "department_id":self.get_department(employee.department_id),
                # 'image': self.get_img_url(employee.id, "hr.employee", "image_medium",
                #                           employee.write_date.replace("-", "").replace(" ", "").replace(":", "")),
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 终审人通过审核
    @http.route('/linkloving_oa_api/action_pass', type='json', auth="none", csrf=False, cors='*')
    def action_pass(self, *kw):
        id = request.jsonrequest.get("id")
        remark = request.jsonrequest.get("remark")
        create_uid = request.jsonrequest.get("create_uid")
        new_commit = request.env['review.process.wizard'].sudo(create_uid).create({
            'remark': remark,
            'material_requests_id': id,
        })
        new_commit.action_oa_pass()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 拒绝
    @http.route('/linkloving_oa_api/action_deny', type='json', auth="none", csrf=False, cors='*')
    def action_deny(self, *kw):
        id = request.jsonrequest.get("id")
        remark = request.jsonrequest.get("remark")
        create_uid = request.jsonrequest.get("create_uid")
        new_commit = request.env['review.process.wizard'].sudo(create_uid).create({
            'remark': remark,
            'material_requests_id': id,
        })
        new_commit.action_oa_deny()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 送审
    @http.route('/linkloving_oa_api/action_to_next', type='json', auth="none", csrf=False, cors='*')
    def action_to_next(self, *kw):
        id = request.jsonrequest.get("id")
        remark = request.jsonrequest.get("remark")
        create_uid = request.jsonrequest.get("create_uid")
        to_last_review = request.jsonrequest.get("to_last_review")
        type = request.jsonrequest.get("type")
        partner_id = request.jsonrequest.get("partner_id")
        new_commit = request.env['review.process.wizard'].sudo(create_uid).create({
            'remark': remark,
            'material_requests_id': id,
            'partner_id': partner_id,
        })
        new_commit.oa_action_to_next(type, to_last_review)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 搜索工程领料单
    @http.route('/linkloving_oa_api/search_material_request', type='json', auth="none", csrf=False, cors='*')
    def search_material_request(self, *kw):
        type = request.jsonrequest.get("type")
        search_text = request.jsonrequest.get("search_text")
        user_id = request.jsonrequest.get("user_id")
        waitme_type = request.jsonrequest.get("waitme_type")
        if (type == "my"):
            material_list = request.env['material.request'].sudo().search(
                [('create_uid', '=', user_id), ('name', 'ilike', search_text)],
                order='id desc')
        elif (type == "already"):
            if (waitme_type == "name"):
                material_list = request.env['material.request'].sudo().search(
                    [("review_i_approvaled_val", "child_of", user_id), ('create_uid', 'ilike', search_text)],
                    order='id desc')
            else:
                material_list = request.env['material.request'].sudo().search(
                    [("review_i_approvaled_val", "child_of", user_id), ('name', 'ilike', search_text)],
                    order='id desc')
        else:
            if (waitme_type == "name"):
                material_list = request.env['material.request'].sudo().search(
                    [('who_review_now_id', '=', user_id), ("picking_state", "=", "review_ing"),
                     ('create_uid', 'ilike', search_text)],
                    order='id desc')
            else:
                material_list = request.env['material.request'].sudo().search(
                    [('who_review_now_id', '=', user_id), ("picking_state", "=", "review_ing"),
                     ('name', 'ilike', search_text)],
                    order='id desc')

        data = []
        for material_request in material_list:
            data.append({
                "name": material_request.name,
                "picking_type": material_request.picking_type,
                "my_create_uid": self.get_department(material_request.my_create_uid),
                "delivery_date": material_request.delivery_date,
                "my_create_date": material_request.my_create_date,
                "picking_state": material_request.picking_state,
                "who_review_now": self.get_department(material_request.who_review_now),
                "picking_cause": material_request.picking_cause,
                "remark": material_request.remark or '无',
                "line_ids": self.change_material_request_line_ids_to_json((material_request.line_ids)),
                "user_ava": LinklovingAppApi.get_img_url(material_request.create_uid.id,
                                                         "res.users", "image_medium"),
                "review_process_line_ids": self.change_shenpi_line_ids_tojson(material_request.review_process_line_ids)
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def change_material_request_line_ids_to_json(self, objs):
        data = []
        for obj in objs:
            data.append({
                "product_id": self.get_department(obj.product_id),
                "product_qty": obj.product_qty,
                "qty_available": obj.qty_available,
                "quantity_done": obj.quantity_done,
            })
        return data

    def change_shenpi_line_ids_tojson(self, objs):
        data = []
        for obj in objs:
            user_ava_id = request.env['res.users'].sudo().search([('partner_id', '=', obj.partner_id.id)])
            data.append({
                "write_uid": self.get_department(obj.partner_id),
                "user_ava": LinklovingAppApi.get_img_url(user_ava_id.id,
                                                         "res.users", "image_medium"),
                "state": obj.state,
                "remark": obj.remark,
                "write_date": obj.write_date,
                "last_review_line_id": obj.last_review_line_id.id,
            })
        data.reverse()
        return data


        #  XD 我的请假

    @http.route('/linkloving_oa_api/get_leavelist', type='json', auth="none", csrf=False, cors='*')
    def get_leavelist(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get('user_id')
        domain = [('user_id', '=', user_id), ('holiday_type', '=', 'employee'),
                  ('holiday_status_id.active', '=', True)]
        orders = request.env['hr.holidays'].sudo().search(domain,
                                                          limit=limit,
                                                          offset=offset,
                                                          order='id desc')
        data = []
        for orderDetail in orders:
            data.append({
                "description": orderDetail.name,
                "date_from": orderDetail.date_from,
                "date_to": orderDetail.date_to,
                "create_date": orderDetail.create_date,
                "holiday_status_id": orderDetail.holiday_status_id.name,
                "state": orderDetail.state,
                "id": orderDetail.id
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

        # 请假详细页

    @http.route('/linkloving_oa_api/get_leavelist_detail', type='json', auth="none", csrf=False, cors='*')
    def get_leavelist_detail(self, *kw):
        id = request.jsonrequest.get('id')
        orderDetail = request.env['hr.holidays'].sudo().browse(id)
        data = {
            "description": orderDetail.name,
            "date_from": orderDetail.date_from,
            "date_to": orderDetail.date_to,
            "create_date": orderDetail.create_date,
            "holiday_status_id": orderDetail.holiday_status_id.name,
            "state": orderDetail.state,
            'message_ids': self.get_leave_record(orderDetail.message_ids),  # 审批请假记录
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

        # 请假审批记录

    def get_leave_record(self, objs):
        data = []
        for obj in objs:
            data.append({
                "create_time": obj.create_date,
                "create_person_ava": LinklovingAppApi.get_img_url(obj.create_uid.self.user_ids.id,
                                                                  "res.users", "image_medium"),
                "create_person": obj.create_uid.display_name,
                "description": obj.description,
                "old_state": obj.tracking_value_ids.old_value_char or '',
                "new_state": obj.tracking_value_ids.new_value_char or '',
            })
        return data

    # 获取休假类型
    @http.route('/linkloving_oa_api/get_leaveType', type='json', auth="none", csrf=False, cors='*')
    def get_leaveType(self, *kw):
        limit = request.jsonrequest.get("limit")
        data = {
            "typeList": self.get_name_id(request.env['hr.holidays.status'].sudo().search([]))
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 我的申请
    @http.route('/linkloving_oa_api/get_applylist', type='json', auth="none", csrf=False, cors='*')
    def get_applylist(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get('user_id')
        type = request.jsonrequest.get('type')
        data = request.jsonrequest.get('data')
        domain = []
        domain.append(('employee_id.user_id', '=', user_id))
        if type == 'number':
            domain.append(('expense_no', 'ilike', data))
        elif type == 'department':
            domain.append(('department_id', 'ilike', data))
        elif type == 'employee':
            domain.append(('employee_id', 'ilike', data))
        orders = request.env['hr.expense.sheet'].sudo().search(domain,
                                                               limit=limit,
                                                               offset=offset,
                                                               order='id desc')
        data = []
        for orderDetail in orders:
            data.append({
                'name': orderDetail.expense_no,
                'department': orderDetail.department_id.display_name,
                "payment": orderDetail.total_amount,
                "create_time": orderDetail.create_date,
                "state": orderDetail.state,
                'id': orderDetail.id
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 申请详细页
    @http.route('/linkloving_oa_api/get_applylist_detail', type='json', auth="none", csrf=False, cors='*')
    def get_applylist_detail(self, *kw):
        id = request.jsonrequest.get('id')
        orderDetail = request.env['hr.expense.sheet'].sudo().browse(id)
        data = {
            'state': orderDetail.state,
            'id': orderDetail.id,
            'name': orderDetail.expense_no,
            'employee': orderDetail.employee_id.display_name,  # 员工
            "pre_payment_reminding": orderDetail.pre_payment_reminding,  # 暂支余额
            "payment": orderDetail.total_amount,  # 总金额
            'expense_line_ids': self.get_expense_line_ids(orderDetail.expense_line_ids, orderDetail),  # 报销明细
            'message_ids': self.get_apply_record(orderDetail.message_ids),  # 审批申请记录
            'department': orderDetail.department_id.display_name,  # 部门
            'department_id': orderDetail.department_id.id,
            'employee_id': orderDetail.employee_id.id,
            'to_approve_name': orderDetail.to_approve_id.name or "",
            'taxList': self.get_name_and_id(request.env['account.tax'].sudo().search([]))
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 申请记录
    def get_apply_record(self, objs):
        data = []
        for obj in objs:
            old_state = obj.tracking_value_ids and obj.tracking_value_ids[0].old_value_char or ''
            new_state = obj.tracking_value_ids and obj.tracking_value_ids[0].new_value_char or ''

            data.append({
                "create_time": obj.create_date,
                "create_person_ava": LinklovingAppApi.get_img_url(obj.create_uid.self.user_ids.id,
                                                                  "res.users", "image_medium"),
                "create_person": obj.create_uid.display_name,
                "description": obj.compyter_body,
                "old_state": old_state,
                "new_state": new_state,
            })
        return data

    # 申请详细条目
    def get_expense_line_ids(self, objs, orderDetail):
        data = []
        for obj in objs:
            data.append({
                'name': obj.product_id.name,
                "description": obj.name,
                "amount": obj.unit_amount,
                "department": orderDetail.department_id.id,
                "employee_id": orderDetail.employee_id.id,
                "productId": obj.product_id.id,
                "id": obj.id,
                "tax": obj.tax_ids.name or '',
                "remarks": obj.description or ""
            })
        return data

    # 获取暂支金额,部门,产品名
    @http.route('/linkloving_oa_api/get_payment_reminding', type='json', auth="none", csrf=False, cors='*')
    def get_payment_reminding(self, *kw):
        id = request.jsonrequest.get('id')
        orderDetail = request.env['hr.expense.sheet'].sudo().browse(id)
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', id)])
        name = request.env['hr.employee'].sudo().search(
            [('user_id', '=', id)]).name
        products = request.env['product.product'].sudo().search(
            [('can_be_expensed', '=', True)])
        taxList = request.env['account.tax'].sudo().search([])
        shengou_amount = self.get_shengou_momey(employee.id)
        data = {
            'pre_payment_reminding': employee.pre_payment_reminding,  # 暂支金额
            'department': self.get_name_and_id(request.env['hr.department'].sudo().search([])),  # 部门
            'product': self.get_name_and_id(products),  # 产品
            'employee_id': employee.id,  # 员工id
            'name': name,  # 姓名
            "taxList": self.get_name_and_id(taxList),  # 税金列表
            'department_id': orderDetail.department_id.id,  # 部门id
            'balance': shengou_amount
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取申购余额
    def get_shengou_momey(self, id):
        employee_id = id
        domain = []
        domain.append(('employee_id', '=', employee_id))
        domain.append(('state', '=', "approve"))
        domain.append(('sheet_id', '=', False))
        orders = request.env['hr.purchase.apply.line'].sudo().search(domain,
                                                                     order='id desc')
        data = []
        amount = 0
        for orderDetail in orders:
            amount = amount + round(orderDetail.price_unit * orderDetail.product_qty, 2)
        return amount

    # 创建报销单/修改完保存
    @http.route('/linkloving_oa_api/create_apply_order', type='json', auth="none", csrf=False, cors='*')
    def create_apply_order(self, *kw):
        data = request.jsonrequest.get("data")
        userId = data.get('user_id')
        is_reset = data.get('is_reset')
        id = data.get('id')
        if is_reset:
            new_order_draft = request.env['hr.expense.sheet'].sudo(userId).browse(id)
            expense_lines = new_order_draft.expense_line_ids
            new_order_draft.write({
                'department_id': data.get('department_id'),  # 部门
                'employee_id': data.get('employee_id'),  # 申请人
                'expense_line_ids': [(0, 0, {
                    'product_id': p.get('product_id'),  # 产品
                    'unit_amount': float(p.get('unit_amount')),  # 金额
                    'name': p.get('name'),  # 费用说明
                    'employee_id': p.get('employee_id'),
                    'department_id': p.get('department_id'),
                    'tax_ids': ([(6, 0, [p.get('taxid')])] if type(p.get('taxid')) == int else [(6, 0, [4])]),
                    'description': p.get('remarks') or '',
                }) for p in data.get('expense_line_ids')]
            })
            for expense_line in expense_lines:
                request.env['hr.expense'].sudo().browse(expense_line.id).unlink()
            new_order_draft.reset_expense_sheets()
        else:
            new_order_draft = request.env['hr.expense.sheet'].sudo(userId).create({
                'department_id': data.get('department_id'),  # 部门
                'employee_id': data.get('employee_id'),  # 申请人
                'expense_line_ids': [(0, 0, {
                    'product_id': p.get('product_id'),  # 产品
                    'unit_amount': float(p.get('unit_amount')),  # 金额
                    'name': p.get('name'),  # 费用说明
                    'employee_id': p.get('employee_id'),
                    'department_id': p.get('department_id'),
                    'tax_ids': ([(6, 0, [p.get('taxid')])] if type(p.get('taxid')) == int else [(6, 0, [4])]),
                    'description': p.get('remarks') or '',
                }) for p in data.get('expense_line_ids')]
            })
        data = {
            "id": new_order_draft.id
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 撤回
    @http.route('/linkloving_oa_api/get_retract', type='json', auth="none", csrf=False, cors='*')
    def get_retract(self, *kw):
        active_id = request.jsonrequest.get("active_id")
        description = request.jsonrequest.get("description")
        user_id = request.jsonrequest.get("user_id")
        new_order_draft = request.env["hr.expense.refuse.wizard"].sudo(user_id).with_context({
            'active_ids': active_id,
        }).create({
            'description': description,  # 理由
        })
        new_order_draft.expense_refuse_reason()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 提交审核
    @http.route('/linkloving_oa_api/submit_apply', type='json', auth="none", csrf=False, cors='*')
    def submit_apply(self, *kw):
        id = request.jsonrequest.get("id")
        user_id = request.jsonrequest.get("user_id")
        new_order_draft = request.env["hr.expense.sheet"].sudo(user_id).browse(id)
        new_order_draft.hr_expense_sheet_post()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 我已审核的申购
    @http.route('/linkloving_oa_api/audited_purchase', type='json', auth="none", csrf=False, cors='*')
    def audited_purchase(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get('user_id')
        type = request.jsonrequest.get('type')
        domain = []
        if type == "wait":
            domain.append(('to_approve_id', '=', user_id))
        elif type == "audited":
            domain.append(('approve_ids', 'child_of', user_id))
        orders = request.env['hr.purchase.apply'].sudo().search(domain,
                                                                limit=limit,
                                                                offset=offset,
                                                                order='id desc')
        data = []
        for orderDetail in orders:
            data.append({
                'apply_date': orderDetail.apply_date,
                'department': orderDetail.department_id.display_name,
                "employee": orderDetail.employee_id.display_name,
                "name": orderDetail.name,
                "state": orderDetail.state,
                "total_amount": orderDetail.total_amount,
                "id": orderDetail.id
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 批准 发送状态的 申购
    @http.route('/linkloving_oa_api/confirm_purchase', type='json', auth="none", csrf=False, cors='*')
    def confirm_purchase(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        reason = request.jsonrequest.get("reason")
        type = request.jsonrequest.get("type")
        domain = [("id", '=', sheet_id)]
        confirm_approve = request.env["hr.purchase.apply"].sudo(user_id).search(domain)
        if type == "submit":
            confirm_approve.manager1_approve()
        elif type == "manager1_approve":
            confirm_approve.manager2_approve()
        elif type == "manager2_approve":
            confirm_approve.manager3_approve()
        if reason:
            confirm_approve.create_message_post(reason)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 申购拒绝
    @http.route('/linkloving_oa_api/refuse_audit', type='json', auth="none", csrf=False, cors='*')
    def refuse_audit(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        refuse_reason = request.jsonrequest.get("reason")
        domain = [("id", '=', sheet_id)]
        shengou = request.env['hr.purchase.apply'].sudo(user_id).search(domain,
                                                                        order='id desc')
        shengou.refuse_payment(refuse_reason);
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

        # 申请详细页

    @http.route('/linkloving_oa_api/get_audit_detail', type='json', auth="none", csrf=False, cors='*')
    def get_audit_detail(self, *kw):
        id = request.jsonrequest.get('id')
        orderDetail = request.env["hr.purchase.apply"].sudo().browse(id)
        data = self.shengou_list_to_json(orderDetail)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

        # 搜索申购单

    @http.route('/linkloving_oa_api/search_shengou2', type='json', auth="none", csrf=False, cors='*')
    def search_shengou2(self, *kw):
        search_text = request.jsonrequest.get('search_text')
        user_id = request.jsonrequest.get('user_id')
        type = request.jsonrequest.get('type')
        domain = []
        domain.append(('name', 'ilike', search_text))
        if type == "wait":
            domain.append(('to_approve_id', '=', user_id))
        elif type == "audited":
            domain.append(('approve_ids', 'child_of', user_id))
        else:
            domain.append(('create_uid', '=', user_id))
        shengoulist = request.env['hr.purchase.apply'].sudo().search(domain,
                                                                     order='id desc')
        data = []
        for orderDetail in shengoulist:
            data.append({
                'apply_date': orderDetail.apply_date,
                'department': orderDetail.department_id.display_name,
                "employee": orderDetail.employee_id.display_name,
                "name": orderDetail.name,
                "state": orderDetail.state,
                "total_amount": orderDetail.total_amount,
                "id": orderDetail.id
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)



        # 报销时选择的申购item

    @http.route('/linkloving_oa_api/get_shengou_item', type='json', auth="none", csrf=False, cors='*')
    def get_shengou_item(self, *kw):
        employee_id = request.jsonrequest.get("employee_id")
        domain = []
        domain.append(('employee_id', '=', employee_id))
        domain.append(('state', '=', "approve"))
        domain.append(('sheet_id', '=', False))
        orders = request.env['hr.purchase.apply.line'].sudo().search(domain,
                                                                     order='id desc')
        data = []
        for orderDetail in orders:
            data.append({
                'orderNumber': orderDetail.name,
                'price_unit': orderDetail.price_unit,
                'product_qty': orderDetail.product_qty,
                "description": orderDetail.description,
                "productionName": orderDetail.product_id.display_name,
                "productionId": orderDetail.product_id.id,

            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    #    暂支

    @http.route('/linkloving_oa_api/get_zanzhi_list', type='json', auth="none", csrf=False, cors='*')
    def get_zanzhi_list(self, *kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        user_id = request.jsonrequest.get('user_id')
        type = request.jsonrequest.get('type')
        domain = []
        if type == "apply":
            domain.append(('employee_id.user_id', '=', user_id))
        elif type == "wait_apply":
            domain.append(('to_approve_id', '=', user_id))
        elif type == "applyed":
            domain.append(('approve_ids', 'child_of', [user_id]))
        orders = request.env['account.employee.payment'].sudo().search(domain,
                                                                       limit=limit,
                                                                       offset=offset,
                                                                       order='id desc')
        data = []
        for orderDetail in orders:
            data.append({
                "create_person_ava": LinklovingAppApi.get_img_url(orderDetail.create_uid.self.user_ids.id,
                                                                  "res.users", "image_medium"),
                "to_approve_id": orderDetail.to_approve_id.display_name or '',
                'id': orderDetail.id,
                'name': orderDetail.name,
                "amount": orderDetail.amount,
                "payment_reminding": orderDetail.payment_reminding,  # 暂支余额
                "pre_payment_reminding": orderDetail.pre_payment_reminding,
                "state": orderDetail.state,
                "apply_date": orderDetail.apply_date,
                "employee": orderDetail.employee_id.display_name,
                "company_id": orderDetail.company_id.display_name,
                "bank_account_id": orderDetail.bank_account_id.display_name or '',
                "remark": orderDetail.remark or '',
                'message_ids': self.get_apply_record(orderDetail.message_ids),  # 审批申请记录
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 查询暂支
    @http.route('/linkloving_oa_api/search_zanzhi_list', type='json', auth="none", csrf=False, cors='*')
    def search_zanzhi_list(self, *kw):
        user_id = request.jsonrequest.get('user_id')
        type = request.jsonrequest.get('type')
        data = request.jsonrequest.get('data')
        text = request.jsonrequest.get('text')
        domain = []
        if type == "apply":
            domain.append(('employee_id.user_id', '=', user_id))
        elif type == "wait_apply":
            domain.append(('to_approve_id', '=', user_id))
        elif type == "applyed":
            domain.append(('approve_ids', 'child_of', [user_id]))
        domain.append((data, 'ilike', text))
        orders = request.env['account.employee.payment'].sudo().search(domain)
        data = []
        for orderDetail in orders:
            data.append({
                "create_person_ava": LinklovingAppApi.get_img_url(orderDetail.create_uid.self.user_ids.id,
                                                                  "res.users", "image_medium"),
                "to_approve_id": orderDetail.to_approve_id.display_name or '',
                'id': orderDetail.id,
                'name': orderDetail.name,
                "amount": orderDetail.amount,
                "pre_payment_reminding": orderDetail.pre_payment_reminding,
                "state": orderDetail.state,
                "payment_reminding": orderDetail.payment_reminding,  # 暂支余额
                "apply_date": orderDetail.apply_date,
                "employee": orderDetail.employee_id.display_name,
                "company_id": orderDetail.company_id.display_name,
                "bank_account_id": orderDetail.bank_account_id.display_name or '',
                "remark": orderDetail.remark or '',
                'message_ids': self.get_apply_record(orderDetail.message_ids),  # 审批申请记录
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)


        # 批准 发送状态的 暂支

    @http.route('/linkloving_oa_api/confirm_zanzhi', type='json', auth="none", csrf=False, cors='*')
    def confirm_zanzhi(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        reason = request.jsonrequest.get("reason")
        type = request.jsonrequest.get("type")
        domain = [("id", '=', sheet_id)]
        confirm_approve = request.env["account.employee.payment"].sudo(user_id).search(domain)
        if type == "confirm":
            confirm_approve.manager1_approve()
        elif type == "manager1_approve":
            confirm_approve.manager2_approve()
        elif type == "manager2_approve":
            confirm_approve.manager3_approve()
        if reason:
            confirm_approve.create_message_post(reason)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # 暂支拒绝
    @http.route('/linkloving_oa_api/refuse_zanzhi', type='json', auth="none", csrf=False, cors='*')
    def refuse_zanzhi(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        refuse_reason = request.jsonrequest.get("reason")
        domain = [("id", '=', sheet_id)]
        shengou = request.env["account.employee.payment"].sudo(user_id).search(domain,
                                                                               order='id desc')
        shengou.refuse_payment(refuse_reason);
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"success": 1})

    # ZWS
    @classmethod
    def blog_to_json(cls, blog_post):
        data = {
            'author_id': blog_post.author_id.id,
            'blog_id': {
                'blog_id': blog_post.blog_id.id,
                'blog_name': blog_post.blog_id.name
            },
            'content': LinklovingOAApi.change_content(blog_post.content),
            'create_date': blog_post.create_date,
            'create_uid': {
                'create_id': blog_post.sudo().create_uid.id,
                'create_name': blog_post.sudo().create_uid.name,
                'create_img': LinklovingAppApi.get_img_url(blog_post.sudo().create_uid.self.user_ids.id, "res.users",
                                                           "image_medium")
            },
            'display_name': blog_post.display_name,
            'id': blog_post.id,
            'name': blog_post.name,
            'published_date': blog_post.published_date,
            'ranking': blog_post.ranking,
            'subtitle': blog_post.subtitle,
            'tag_ids': {
                'tag_id': blog_post.tag_ids.id if blog_post.tag_ids else "",
                'tag_name': blog_post.tag_ids.name if blog_post.tag_ids else ""
            },
            'visits': blog_post.visits,
        }

        return data

    # 转化content
    @classmethod
    def change_content(cls, blog_content):
        content = pq(blog_content)
        if content('img'):
            for a_html in content('img'):
                # attachment_one = Model_Attachment.search([('datas', '=', pq(a_html).attr('src').split('base64,')[1])])
                # if not attachment_one:
                pq(a_html).attr('src', request.httprequest.host_url[:-1] + str(pq(a_html).attr('src')))
        elif content('a'):
            for a_html in content('a'):
                # attachment_one = Model_Attachment.search([('datas', '=', pq(a_html).attr('src').split('base64,')[1])])
                # if not attachment_one:

                pq(a_html).attr('href', request.httprequest.host_url[:-1] + str(pq(a_html).attr('href')))
        else:
            content = content
        return str(content)

    # 获取blog列（热门和全部）
    @http.route('/linkloving_oa_api/get_blog_list', type='json', auth='none', csrf=False, cors='*')
    def get_blog_list(self, **kw):
        type = request.jsonrequest.get('type')
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        search_body = request.jsonrequest.get('search_body')
        tag_id = request.jsonrequest.get('tag_id')
        is_tag_id = request.jsonrequest.get('is_tag_id')
        is_first = request.jsonrequest.get('is_first')
        if not limit:
            limit = 60
        if not offset:
            offset = 0
        blog_list_json = []
        domain = [('website_published', '=', True)]
        if type == 'all':
            blog_list = request.env['blog.post'].search(domain, limit=limit, offset=offset)
            for blog_list_bean in blog_list:
                blog_list_json.append(LinklovingOAApi.blog_to_json(blog_list_bean))
        elif type == 'hot':
            blog_list = request.env['blog.post'].search(domain, limit=10, offset=offset, order='visits desc')
            for blog_list_bean in blog_list:
                blog_list_json.append(LinklovingOAApi.blog_to_json(blog_list_bean))
        elif type == 'search':
            blog_list = request.env['blog.post'].search(
                [('website_published', '=', True), ('name', 'ilike', search_body)])
            for blog_list_bean in blog_list:
                blog_list_json.append(LinklovingOAApi.blog_to_json(blog_list_bean))
        elif is_tag_id:
            if is_first:
                blog_list = request.env['blog.post'].search(
                    [('website_published', '=', True), ('blog_id', '=', int(tag_id))])
            else:
                blog_list = request.env['blog.post'].search(
                    [('website_published', '=', True), ('tag_ids', '=', int(tag_id))])
            for blog_list_bean in blog_list:
                blog_list_json.append(LinklovingOAApi.blog_to_json(blog_list_bean))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=blog_list_json)

    # 获取博客分类
    @http.route('/linkloving_oa_api/get_blog_colum', type='json', auth='none', csrf=False, cors='*')
    def get_blog_colum(self, **kw):
        blog_list = request.env['blog.blog'].search([])
        colum_blog_list = []
        for blog_list_bean in blog_list:
            colum_blog_list.append(LinklovingOAApi.colum_blog_to_json(blog_list_bean))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=colum_blog_list)

    # 博客分类json转化
    @classmethod
    def colum_blog_to_json(cls, blog_blog):
        data = {
            'create_date': blog_blog.create_date,
            'create_uid': {
                'create_id': blog_blog.sudo().create_uid.id,
                'create_name': blog_blog.sudo().create_uid.name

            },
            'is_all_blog': blog_blog.is_all_blog,
            'display_name': blog_blog.display_name,
            'id': blog_blog.id,
            'name': blog_blog.name
            ,
            'subtitle': blog_blog.subtitle,
            'blog_tag_ids': [
                {'tag_id': blog_tag_bean.id,
                 'tag_name': blog_tag_bean.name
                 }
                for blog_tag_bean in blog_blog.blog_tag_ids],
        }
        return data
