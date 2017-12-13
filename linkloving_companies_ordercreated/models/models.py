# -*- coding: utf-8 -*-
import json

import requests
from requests import ConnectionError

from odoo import models, fields, api
from odoo.exceptions import UserError


class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    sub_company = fields.Selection(string=u'附属公司类型', selection=[('normal', u'正常'),
                                                                ('sub', u'子公司'),
                                                                ('main', u'下单公司')],
                                   default="normal")
    request_host = fields.Char(string=u'请求地址(包含端口)')
    db_name = fields.Char(string=u'账套名称')
    discount_to_sub = fields.Float(string=u'成本折算率', default=0.8, help=u"跨系统生成的so单单价 = 当前成本/折算率")

class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'

    def get_precost_price(self):
        if self.partner_id.sub_company == 'sub':
            response = self.request_to_get_price()
            if response:
                order_line = response.get("order_line")
                self.write({
                    'order_line': order_line
                })
            else:
                raise UserError(u'未收到返回')
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"成功",
                "text": u"价格更新成功",
                "sticky": False
            }
        }
    def button_confirm(self):
        # todo
        res = super(PurchaseOrderExtend, self).button_confirm()
        if self.partner_id.sub_company == 'sub':
            response = self.request_to_create_so()
            if response:
                pass
                # order_line = response.get("order_line")
                # self.write({
                #     'order_line': order_line
                # })
            else:
                raise UserError(u'未收到返回')
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"操作成功",
                "text": u"自动创建销售单成功! 单号为:%s" % response.get("so"),
                "sticky": False
            }
        }

    def get_request_info(self, str):
        host = self.partner_id.request_host
        if not host.startswith("http://"):
            host = "http://" + host
        url = host + str
        db = self.partner_id.db_name
        header = {'Content-Type': 'application/json'}
        return url, db, header

    def request_to_get_price(self):
        line_list = []
        for order_line in self.order_line:
            line_list.append({
                "line_id": order_line.id,
                "default_code": order_line.product_id.default_code,
            })
        url, db, header = self.get_request_info('/linkloving_web/precost_price')
        response = requests.post(url, data=json.dumps({
            "db": db,
            "discount_to_sub": self.partner_id.discount_to_sub,
            "vals": line_list,
        }), headers=header)
        res_json = json.loads(response.content).get("result")
        if res_json and res_json.get("code") < 0:
            raise UserError(res_json.get("msg"))
        return res_json

    def request_to_create_so(self):
        so = self._prepare_so_values()  # 解析采购单,生成so单信息
        host = self.partner_id.request_host
        url, db, header = self.get_request_info('/linkloving_web/create_order')
        try:
            response = requests.post(url, data=json.dumps({
                # "discount_to_sub": self.partner_id.discount_to_sub,
                "db": db,
                "vals": so,
            }), headers=header)
            res_json = json.loads(response.content).get("result")
            if res_json and res_json.get("code") < 0:
                raise UserError(res_json.get("msg"))
            return res_json
        except ConnectionError:
            raise UserError(u"请求地址错误, 请确认")

    def _prepare_so_values(self):
        # if self.order_line.procurement_ids:
        #     origin = ''
        #     for procurement in self.order_line.procurement_ids:
        #         if procurement.move_dest_id and \
        #                 procurement.move_dest_id.procurement_id and \
        #                 procurement.move_dest_id.procurement_id.sale_line_id:
        #             order_id = procurement.move_dest_id.procurement_id.sale_line_id.order_id
        #             origin += order_id.name or '' + ':' + self.name + ":" + order_id.partner_id.name + ', '
        origin_so = self.env["sale.order"].search([("name", "=", self.first_so_number)])
        data = {
            'remark': self.first_so_number or '' + ':' + self.name + ':' + origin_so.partner_id.name or '',
        }
        line_list = []
        for order_line in self.order_line:
            line_list.append({
                "line_id": order_line.id,
                "default_code": order_line.product_id.default_code,
                "product_name": order_line.product_id.name,
                "product_uom_qty": order_line.product_qty,
                "price_unit": order_line.price,
            })
        data["order_line"] = line_list
        return data
