# -*- coding: utf-8 -*-
import json
import logging

import requests
from requests import ConnectionError

from odoo import models, fields, api, registry
from odoo.exceptions import UserError


class StockPickingExtend(models.Model):
    _inherit = 'stock.picking'

    feedback_id_from_sub = fields.Integer(string=u'对应子系统的品检单id')
    feedback_name_from_sub = fields.Char(string=u'对应子系统的品检单号')


class SubCompanyTransfer(models.Model):
    _name = 'sub.company.transfer'

    feedback_id = fields.Many2one('mrp.qc.feedback', string=u'品检单')
    product_qty = fields.Float(string=u'数量')

    def tranfer_in_sub_sub(self, db_name, feedback_id):
        cr = registry(db_name).cursor()
        self = self.with_env(self.env(cr=cr))  # TDE FIXME
        feedback = self.env["mrp.qc.feedback"].sudo().search([('id', '=', int(feedback_id))])
        return feedback


    def get_request_info(self, str1):
        origin_sale_id = self.feedback_id.production_id.origin_sale_id
        if not origin_sale_id:
            raise UserError(u'未找到源SO单据')

        if not origin_sale_id.partner_id.main_company_id:
            raise UserError(u"未设置主公司信息")

        host = origin_sale_id.partner_id.main_company_id.host_correct
        url = host + str1
        db = origin_sale_id.partner_id.main_company_id.db_name
        header = {'Content-Type': 'application/json'}
        return url, db, header

    def handle_response(self, response):
        res_json = json.loads(response.content).get("result")
        res_error = json.loads(response.content).get("error")
        if res_json and res_json.get("code") < 0:
            raise UserError(res_json.get("msg"))
        if res_error:
            raise UserError(res_error.get("data").get("message"))
        return res_json

    # 自动出库
    def action_transfer_out_automatic(self):
        origin_sale_id = self.feedback_id.production_id.origin_sale_id
        if origin_sale_id:
            picking_to_out = origin_sale_id.picking_ids.filtered(
                lambda x: x.state not in ["done", "cancel"] and x.picking_type_code == 'internal')
            if picking_to_out:
                self.picking_transfer_out_auto(picking_to_out)
            picking_to_out_2 = origin_sale_id.picking_ids.filtered(
                lambda x: x.state not in ["done", "cancel"] and x.picking_type_code == 'outgoing')
            if picking_to_out_2:
                self.picking_transfer_out_auto(picking_to_out_2)

    def picking_transfer_out_auto(self, picking_to_out):
        if picking_to_out.state != 'assigned':
                picking_to_out.force_assign()
        if len(picking_to_out) == 1:
            op_to_do = self.env["stock.pack.operation"]
            for op in picking_to_out.pack_operation_product_ids:
                if op.product_id.id == self.feedback_id.product_id.id:  # 找到对应的产品
                    op_to_do = op
                    break
            if op_to_do:  # 若找到了
                op_to_do.qty_done = self.feedback_id.qty_produced
                logging.warning(u"op_to_do.qty_done ===%s" % str(op_to_do.qty_done))
            else:
                raise UserError(u'找不到对应的出货条目')
        else:
            raise UserError(u'找不到对应的出货单或者出货单数量状态异常')
        confirmation = self.env["stock.backorder.confirmation"].create({
            'pick_id': picking_to_out.id
        })
        picking_to_out.check_backorder()
        confirmation.process()
        picking_to_out.to_stock()

    def action_transfer_in_automatic(self):
        origin_sale_id = self.feedback_id.production_id.origin_sale_id
        if not origin_sale_id.po_name_from_main:
            raise UserError(u'未找到下单公司PO号')
        url, db, header = self.get_request_info('/linkloving_web/transfer_in')
        vals = {
            'db': db,
            'vals': {
                'po_name': origin_sale_id.po_name_from_main or '',
                'default_code': self.feedback_id.product_id.default_code,
                'product_qty': self.feedback_id.qty_produced,
                'feedback_id_from_sub': self.feedback_id.id,
                'feedback_name_from_sub': self.feedback_id.name,
            }
        }
        response = requests.post(url, data=json.dumps(vals), headers=header)
        res = self.handle_response(response)
        if res:
            vals = res.get("vals")
            self.feedback_id.write({
                'picking_id_from_main': vals.get("picking_id_from_main"),
                'picking_name_from_main': vals.get("picking_name_from_main"),
            })
        else:
            raise UserError(u"未收到数据返回")

    def make_transfer(self):
        """
        当子系统品检单入库的时候, 子系统销售单自动出库, 主系统采购单自动入库
        :return:
        """
        # 子系统销售单自动出库
        self.action_transfer_out_automatic()
        # 主系统采购单自动入库
        self.action_transfer_in_automatic()


class MrpQcFeedbackExtend(models.Model):
    _inherit = 'mrp.qc.feedback'

    picking_id_from_main = fields.Integer(string=u'对应主系统的入库单ID')
    picking_name_from_main = fields.Char(string=u'对应主系统的入库单号')

    def action_post_inventory(self):
        res = super(MrpQcFeedbackExtend, self).action_post_inventory()
        if self._context.get("from_sub"):
            if not self.production_id.origin_sale_id:
                origin = self.production_id.origin
                sale_id = self.env["sale.order"].search([("name", "=", origin)], limit=1)
            else:
                sale_id = self.production_id.origin_sale_id

            if sale_id and sale_id.partner_id.sub_company == 'main':
                trans = self.env['sub.company.transfer'].create({
                    'feedback_id': self.id,
                    'product_qty': self.qty_produced,
                })
                trans.make_transfer()
            else:
                raise UserError(u'只有下单公司才能执行此操作')
        return res
