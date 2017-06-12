# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import urllib

class linkloving_mrp_automatic_plan(models.Model):
    _name = 'linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

    @api.multi
    def get_holiday(self):
        page = urllib.urlopen(
            "https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?query=2017%E5%B9%B48%E6%9C%88&co=&resource_id=6018&t=1496889566304&ie=utf8&oe=gbk&format=json&tn=baidu&_=1496889558209")
        html = page.read()
        # print html.decode("gbk")
        return {
            "holiday": html.decode("gbk")
        }

    def calc_status_light(self):
        pass

class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    prepare_time = fields.Integer(u"准备时间 (秒)")
    capacity_value = fields.Integer(u"产能 (pcs/s)")


    # class PuchaseOrderEx(models.Model):
    #     _inherit = "purchase.order"
    #
    #     status_light = fields.Selection(string="状态灯", selection=[('0', '红'),
    #                                                              ('1', '黄'),
    #                                                              ('2','绿') ], required=False, )
    #
    # class SaleOrderEx(models.Model):
    #     _inherit = "sale.order"
    #
    #     status_light = fields.Selection(string="状态灯", selection=[('0', '红'),
    #                                                              ('1', '黄'),
    #                                                              ('2','绿') ], required=False, )
    # class MrpProductionEx(models.Model):
    #     _inherit = "mrp.production"
    #
    #     status_light = fields.Selection(string="状态灯", selection=[('0', '红'),
    #                                                              ('1', '黄'),
    #                                                              ('2','绿') ], required=False, )
