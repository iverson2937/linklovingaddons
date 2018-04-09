# -*- coding: utf-8 -*-
import json

import requests
from requests import ConnectionError

from odoo import models, fields, api
from odoo.exceptions import UserError


class FollowOrderPartner(models.Model):
    _name = 'follow.order.partner'

    @api.multi
    def name_get(self):
        return [(partner.id, '%s - %s' % (partner.prefix_name or '', partner.follow_partner_id.name))
                for partner in self]

    prefix_name = fields.Char(string=u'名称')
    follow_partner_id = fields.Many2one('res.partner', string=u'跟单员')


class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    sub_company = fields.Selection(string=u'附属公司类型', selection=[('normal', u'正常'),
                                                                ('sub', u'子公司'),
                                                                ('main', u'下单公司')],
                                   default="normal")
    sub_company_id = fields.Many2one('sub.company.info', string=u'公司信息')
    main_company_id = fields.Many2one('sub.company.info', string=u'下单公司信息')

    follow_partner_id = fields.Many2one('follow.order.partner', string=u'跟单员')
    discount_to_sub = fields.Float(string=u'成本折算率', default=0.8, help=u"跨系统生成的so单单价 = 当前成本/折算率")


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    po_name_from_main = fields.Char(string=u'主系统的po单号')
    so_name_from_main = fields.Char(string=u'主系统的so单号')
    pi_name_from_main = fields.Char(string=u'主系统的PI号')
    order_date_from_main = fields.Char(string=u'订单交期')
    follow_partner_name_from_main = fields.Char(string=u'跟单员')
    sale_man_from_main = fields.Char(string=u'业务员')
    partner_name_from_main = fields.Char(string=u'客户名称')
    order_type_from_main = fields.Char(string=u'订单类型')


class SubCompanyInfo(models.Model):
    _name = 'sub.company.info'

    @api.multi
    def _compute_host_correct(self):
        for info in self:
            host = info.host
            if not host.startswith("http://"):
                host = "http://" + host
            info.host_correct = host

    name = fields.Char(string=u'名称')
    host = fields.Char(string=u'请求地址(包含端口)')
    host_correct = fields.Char(compute='_compute_host_correct')
    db_name = fields.Char(string=u'账套名称')

    def get_request_info(self, str1):
        """

        :param str1:
        :return: url,db,header
        """
        if not self:
            raise UserError(u"未设置子公司信息")

        url = self.host_correct + str1
        db = self.db_name
        header = {'Content-Type': 'application/json'}
        return url, db, header


class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'

    sub_company = fields.Selection(string=u'附属公司类型', related="partner_id.sub_company")
    so_id_from_sub = fields.Integer(string=u'关联的id')
    so_name_from_sub = fields.Char(string=u'关联的子系统so单号')

    def get_precost_price(self):
        if self.state not in ['draft', 'make_by_mrp']:
            raise UserError(u'只有询价单状态才能获取最新价格')
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
                "text": u"价格更新成功\n",
                "sticky": False
            }
        }
    def button_confirm(self):
        res = super(PurchaseOrderExtend, self).button_confirm()
        if self.partner_id.sub_company == 'sub':
            response = self.request_to_create_so()
            if response:
                self.write({
                    'so_id_from_sub': response.get("so_id"),
                    'so_name_from_sub': response.get("so")
                })
                a_url = u"%s/web?#id=%d&view_type=form&model=sale.order" % (
                    self.partner_id.sub_company_id.host_correct, response.get("so_id"))
                return {
                    "type": "ir.actions.client",
                    "tag": "action_notify",
                    "params": {
                        "title": u"操作成功",
                        "text": u"自动创建销售单成功! 对应单号为: <a target='_blank' href=%s>%s</a>" % (a_url, response.get("so")),
                        "sticky": False
                    }
                }
                # order_line = response.get("order_line")
                # self.write({
                #     'order_line': order_line
                # })
            else:
                raise UserError(u'未收到返回')
        return res

    def request_to_get_price(self):
        line_list = []
        for order_line in self.order_line:
            line_list.append({
                "line_id": order_line.id,
                "default_code": order_line.product_id.default_code,
            })
        url, db, header = self.partner_id.sub_company_id.get_request_info('/linkloving_web/precost_price')
        response = requests.post(url, data=json.dumps({
            "db": db,
            "discount_to_sub": self.partner_id.discount_to_sub,
            "vals": line_list,
        }), headers=header)
        return self.handle_response(response)

    def request_to_create_so(self):
        so = self._prepare_so_values()  # 解析采购单,生成so单信息
        url, db, header = self.partner_id.sub_company_id.get_request_info('/linkloving_web/create_order')
        try:
            response = requests.post(url, data=json.dumps({
                # "discount_to_sub": self.partner_id.discount_to_sub,
                "db": db,
                "vals": so,
            }), headers=header)
            return self.handle_response(response)
        except ConnectionError:
            raise UserError(u"请求地址错误, 请确认")

    def handle_response(self, response):
        res_json = json.loads(response.content).get("result")
        res_error = json.loads(response.content).get("error")
        msg = None
        if res_json and res_json.get("code") < 0:
            msg = res_json.get("msg")
        if res_error:
            msg = res_error.get("data").get("message")
        if msg:
            raise UserError(msg)
        return res_json

    def _prepare_so_values(self):
        origin_so = self.env["sale.order"].search([("name", "=", self.first_so_number)])
        data = {
            'remark': (self.first_so_number or '') + ':' + self.name + ':' + (origin_so.partner_id.name or ''),
            'po_name_from_main': self.name,
            'so_name_from_main': self.first_so_number or '',
            'pi_name_from_main': origin_so.pi_number or '',
            'order_date_from_main': self.handle_date,
            'validity_date': self.handle_date,
            'follow_partner_name_from_main': self.partner_id.follow_partner_id.follow_partner_id.name or '',
            'sale_man_from_main': origin_so.user_id.name or '',
            'partner_name_from_main': origin_so.partner_id.name or ''
        }
        line_list = []
        for order_line in self.order_line:
            line_list.append({
                "line_id": order_line.id,
                "default_code": order_line.product_id.default_code,
                "product_name": order_line.product_id.name,
                "product_uom_qty": order_line.product_qty,
                "price_unit": order_line.price_unit,
            })
        data["order_line"] = line_list
        return data
