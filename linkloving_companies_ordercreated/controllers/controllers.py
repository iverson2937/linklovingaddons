# -*- coding: utf-8 -*-
import json
import logging

import requests
from psycopg2._psycopg import OperationalError

from odoo import http, registry
from odoo.exceptions import UserError
from odoo.http import request
import base64


class LinklovingCompanies(http.Controller):
    @classmethod
    def get_qc_img_url(cls, worker_id, ):
        # DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        imgs = []
        for img_id in worker_id:
            url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
                request.httprequest.host_url, str(img_id), 'qc.feedback.img', 'qc_img')
            imgs.append(url)
        return imgs

    def convert_qc_feedback_to_json(self, qc_feedback):
        data = {
            'feedback_id': qc_feedback.id,
            'name': qc_feedback.name,
            'production_id': {
                "order_id": qc_feedback.sudo().production_id.id,
                "display_name": qc_feedback.sudo().production_id.display_name,
                'product_id': {
                    'product_id': qc_feedback.product_id.id,
                    'product_name': qc_feedback.product_id.name,
                    'area_name': qc_feedback.product_id.area_id.name or '',
                },
            },
            'state': qc_feedback.state,
            'qty_produced': qc_feedback.qty_produced,
            'qc_test_qty': qc_feedback.qc_test_qty,
            'qc_rate': qc_feedback.qc_rate,
            'qc_fail_qty': qc_feedback.qc_fail_qty,
            'qc_fail_rate': qc_feedback.qc_fail_rate,
            'qc_note': qc_feedback.qc_note or '',
            'qc_img': LinklovingCompanies.get_qc_img_url(qc_feedback.qc_imgs.ids),
        }
        return data

    @classmethod
    def change_db(cls, db_name):
        request.session.db = db_name  # 设置账套
        request.params["db"] = db_name
        cr = registry(db_name).cursor()
        request.env.cr = cr

    @http.route('/linkloving_web/get_report', auth='none', type='json', csrf=False)
    def get_report(self):
        return request.env["sub.company.report"].sudo().get_report()

    @http.route('/linkloving_web/get_sub_company_report', auth='none', type='json', csrf=False)
    def get_sub_company_report(self):
        so_id = request.jsonrequest.get("so_id")
        return request.env["sub.company.report"].sudo().get_sub_company_report(so_id=so_id)

    @http.route('/linkloving_web/view_feedback_detail', auth='none', type='json', csrf=False)
    def view_feedback_detail(self):
        encode_data = request.jsonrequest.get("data")  # 加密数据
        decode_data = base64.b64decode(encode_data)
        data = json.loads(decode_data)
        if not data.get("db"):
            raise UserError(u'未找到账套信息')
        if not data.get("feedback_id"):
            raise UserError(u'品检单为空')
        feedback_id = data.get("feedback_id")
        try:
            request.session.db = data.get("db")  # 设置账套
            request.params["db"] = data.get("db")
            feedback = request.env["sub.company.transfer"].sudo().tranfer_in_sub_sub(data.get("db"), feedback_id)
            f_dic = self.convert_qc_feedback_to_json(feedback)
        except Exception, e:
            raise e
        return {'feedback': f_dic}

    @http.route('/linkloving_web/do_eco', auth='none', type='json', csrf=False)
    def do_eco(self):
        db = request.jsonrequest.get("db")  # 所选账套
        vals = request.jsonrequest.get("vals")  # 所选账套
        request.session.db = db  # 设置账套
        request.params["db"] = db

        so_name = vals.get("so_name")
        so_id = vals.get("so_id")
        try:
            so_need_change = request.env["sale.order"].sudo().browse(int(so_id))
        except OperationalError:
            return {
                "code": -2,
                "msg": u"账套%s不存在" % db
            }
        if so_need_change.name != so_name:
            return {
                "code": -3,
                "msg": u"子系统销售单号与主系统记录的单号不符, %s->%s" % (so_name, so_need_change.name)
            }
        if so_need_change.partner_id.sub_company != 'main':
            return {
                "code": -4,
                "msg": u"子系统销售单的客户异常,请检查",
            }

        stock_picking_cancel = request.env['ll.stock.picking.cancel'].sudo()
        product_product = request.env["product.product"].sudo()
        cancel_picking = so_need_change.picking_ids.filtered(lambda x: x.state not in ["done", "cancel"])
        if cancel_picking:
            cancel_lines_list = vals.get("cancel_lines_list")
            tmp_list = []
            try:
                line_dic = self.sale_order_line_info_dic(so_need_change)
                move_dic = self.picking_move_info_dic(cancel_picking)
                for line in cancel_lines_list:
                    p_id = product_product.search([('default_code', '=', line.get("default_code"))])
                    if not p_id:
                        return {
                            "code": -6,
                            "msg": u"子系统中找不到对应的料号 %s" % line.get("default_code"),
                        }
                    order_line_info = line_dic.get(line.get("default_code"))
                    move_info = move_dic.get(line.get("default_code"))
                    if not move_info:
                        raise UserError(u'请检查子系统中对应的出货单是否正常!')
                    tmp_list.append((0, 0, {
                        'product_id': p_id.id,
                        'cancel_qty': line.get("cancel_qty"),
                        'total_qty': order_line_info.product_uom_qty,
                        'done_qty': order_line_info.qty_delivered,
                        'product_uom': move_info.product_uom.id,
                        'product_uom_qty': move_info.product_uom_qty,
                        'move_id': move_info.id,
                    }))
                cancel_order = stock_picking_cancel.create({
                    'picking_id': cancel_picking[0].id,
                    'sale_id': so_id,
                    'cancel_line_ids': tmp_list
                })
                cancel_order.confirm_eco_split_move()
            except Exception, e:
                raise e

        else:
            return {
                "code": -5,
                "msg": u"子系统中未找到可操作的调拨单",
            }
        return {
            "code": 1
        }

    def sale_order_line_info_dic(self, so_need_change):
        tmp_dic = {}
        for line in so_need_change.order_line:
            tmp_dic[line.product_id.default_code] = line
        return tmp_dic

    def picking_move_info_dic(self, picking):
        tmp_dic = {}
        for line in picking.move_lines:
            tmp_dic[line.product_id.default_code] = line
        return tmp_dic
    @http.route('/linkloving_web/action_transfer_from_sub', auth='none', type='json', csrf=False)
    def action_transfer_from_sub(self):
        encode_data = request.jsonrequest.get("data")  # 加密数据
        decode_data = base64.b64decode(encode_data)
        data = json.loads(decode_data)
        if data.get("db"):
            request.session.db = data.get("db")  # 设置账套
            request.params["db"] = data.get("db")
        else:
            raise UserError(u'未找到账套信息')

        feedback_id = data.get("feedback_id")
        try:
            feedback = request.env["mrp.qc.feedback"].sudo().browse(int(feedback_id))
            if feedback:
                if feedback.state != 'qc_success':
                    raise UserError(u'此状态不能进行入库操作')
                feedback.with_context({'from_sub': True}).action_post_inventory()
                f_dic = self.convert_qc_feedback_to_json(feedback)
            else:
                raise UserError(u'未找到对应的品检单')
        except Exception, e:
            raise e
        return {'feedback': f_dic}

    @http.route('/linkloving_web/transfer_in', auth='none', type='json', csrf=False, methods=['POST'])
    def transfer_in(self, **kw):
        db = request.jsonrequest.get("db")  # 所选账套
        request.session.db = db  # 设置账套
        request.params["db"] = db

        vals = request.jsonrequest.get("vals")  # 需要查询的产品数据
        try:
            default_code = vals.get("default_code")
            p_obj = request.env["product.product"].sudo().search([("default_code", "=", default_code)])
        except OperationalError:
            return {
                "code": -2,
                "msg": u"账套%s不存在" % db
            }
        if not p_obj:
            return {
                "code": -4,
                "msg": u"%s此料号在%s账套中找不到" % (default_code, db)
            }

        po_name = vals.get("po_name")
        product_qty = vals.get("product_qty")
        po = request.env["purchase.order"].sudo().search([('name', '=', po_name)])
        if not po:
            return {
                "code": -5,
                "msg": u"%s此采购单在%s账套中找不到" % (po_name, db)
            }
        picking_to_in = po.picking_ids.filtered(
            lambda x: x.state not in ["done", "cancel"] and x.picking_type_code == 'internal')  # 对应子系统入库的单子
        if picking_to_in:
            self.picking_tranfer_in_auto(picking_to_in, po_name, p_obj, product_qty)
            picking_to_in.write({
                'feedback_name_from_sub': vals.get("feedback_name_from_sub"),
                'feedback_id_from_sub': vals.get("feedback_id_from_sub")
            })
        picking_to_in2 = po.picking_ids.filtered(
            lambda x: x.state not in ["done", "cancel"] and x.picking_type_code == 'incoming')  # 对应子系统入库的单子
        if picking_to_in2:
            self.picking_tranfer_in_auto(picking_to_in2, po_name, p_obj, product_qty)
            picking_to_in2.write({
                'feedback_name_from_sub': vals.get("feedback_name_from_sub"),
                'feedback_id_from_sub': vals.get("feedback_id_from_sub")
            })
        return {
            "code": 1,
            "vals": {
                'picking_id_from_main': picking_to_in.id,
                'picking_name_from_main': picking_to_in.name,
            }
        }

    def picking_tranfer_in_auto(self, pickings_to_do, po_name, p_obj, product_qty):
        for picking_to_in in pickings_to_do:
            if len(picking_to_in) != 1:
                return {
                    "code": -6,
                    "msg": u"%s此采购单出货单异常" % (po_name)
                }
            op_to_do = request.env["stock.pack.operation"]
            for op in picking_to_in.pack_operation_product_ids:
                if op.product_id.id == p_obj.id:  # 找到对应的产品
                    op_to_do = op
                    break
            op_to_do.qty_done = product_qty
            try:
                confirmation = request.env["stock.backorder.confirmation"].sudo().create({
                    'pick_id': picking_to_in.id
                })
                if picking_to_in.state != 'assigned':
                    picking_to_in.force_assign()
                confirmation.process()
                picking_to_in.to_stock()
            except Exception, e:
                raise e

    @http.route('/linkloving_web/precost_price', auth='none', type='json', csrf=False, methods=['POST'])
    def precost_price(self, **kw):
        db = request.jsonrequest.get("db")  # 所选账套
        request.session.db = db  # 设置账套
        request.params["db"] = db

        vals = request.jsonrequest.get("vals")  # 需要查询的产品数据
        discount_to_sub = request.jsonrequest.get("discount_to_sub")  # 折算率
        data_return = []
        for val in vals:
            default_code = val["default_code"]
            try:
                p_obj = request.env["product.product"].sudo().search([("default_code", "=", default_code)])
            except OperationalError:
                return {
                    "code": -2,
                    "msg": u"账套%s不存在" % db
                }
            if not p_obj:
                return {
                    "code": -4,
                    "msg": u"%s此料号在%s账套中找不到" % (default_code, db)
                }
            data_return.append((1, val["line_id"], {
                'line_id': val["line_id"],
                'price_unit': p_obj.pre_cost_cal() / discount_to_sub
            }))

        return {
            "code": 1,
            'order_line': data_return,
        }

    @http.route('/linkloving_web/create_order', auth='none', type='json', csrf=False, methods=['POST'])
    def ll_call_kw(self, **kw):
        db = request.jsonrequest.get("db")  # 所选账套
        vals = request.jsonrequest.get("vals")  # so的数据
        # discount_to_sub = request.jsonrequest.get("discount_to_sub")  # 折算率
        request.session.db = db  # 设置账套
        request.params["db"] = db
        try:  #获取下单公司信息
            partner = request.env["res.partner"].sudo().search([("sub_company", "=", "main")], limit=1)
            if partner:
                vals["partner_id"] = partner.id
            else:
                return {
                    "code": -3,
                    "msg": u"未设置下单公司"
                }
        except OperationalError:
            return {
                "code": -2,
                "msg": u"账套%s不存在" % db
            }
        try:#创建so
            order_line_vals = vals["order_line"]
            order_line = []
            # order_line_return = []  #往回传的line信息
            for line in order_line_vals:
                default_code = line["default_code"]
                if not default_code:
                    return {
                        "code": -6,
                        "msg": u'料号异常不能为空 %s' % json.dumps(line)
                    }
                p_obj = request.env["product.product"].sudo().search([("default_code", "=", default_code)])
                if not p_obj:
                    return {
                        "code": -4,
                        "msg": u"%s此料号在%s账套中找不到" % (default_code, db)
                    }
                if len(p_obj) > 1:
                    return {
                        "code": -5,
                        "msg": u'%s 此料号在子系统中对应了多个产品' % (json.dumps(line))
                    }
                # price_after_dis = p_obj.pre_cost_cal() / discount_to_sub
                one_line_val = {
                    'product_id': p_obj.id,
                    'product_uom': p_obj.uom_id.id,
                    'product_uom_qty': line["product_uom_qty"],
                    'price_unit': line["price_unit"],
                }
                # order_line_return.append((1, line["line_id"], {
                #     # 'line_id': line["line_id"],
                #     'price_unit': price_after_dis
                # }))
                order_line.append([0, False, one_line_val])
            vals["order_line"] = order_line
            so = request.env["sale.order"].sudo().create(vals)
            return {
                "code": 1,
                'so': so.name,
                'so_id': so.id,
                # 'order_line': order_line_return,
            }
        except Exception, e:

            return {
                "code": -1,
                "msg": u"创建订单出现异常, %s" % (e.name if hasattr(e, "name") else e),
            }

    @http.route('/linkloving_web/get_stand_price', auth='none', type='json', csrf=False, methods=['POST'])
    def get_stand_price(self, **kw):
        db = request.jsonrequest.get("db")  # 所选账套
        request.session.db = db  # 设置账套
        request.params["db"] = db

        vals = request.jsonrequest.get("vals")  # 需要查询的产品数据
        p_obj = request.env["product.product"].sudo().search([("default_code", "in", vals)])
        data_return = []
        try:
            for p in p_obj:
                data_return.append({
                    'default_code': p.default_code,
                    'price_unit': p.pre_cost_cal()
                })
        except Exception, e:
            return {
                "code": -2,
                "msg": u"出现异常 %s" % e.name
            }
        return {
            "code": 1,
            'vals': data_return,
        }
