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

class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    prepare_time = fields.Integer(u"准备时间 (秒)")
    capacity_value = fields.Integer(u"产能 (pcs/s)")
