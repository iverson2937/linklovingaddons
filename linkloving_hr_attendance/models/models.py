# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Linklovinr_hr_attendance(models.Model):
     _inherit = 'hr.attendance'
     company_name = fields.Char(string="打卡所在地")
     # name = fields.Char()
     # value = fields.Integer()
     # value2 = fields.Float(compute="_value_pc", store=True)
     # description = fields.Text()

     # @api.depends('value')
     # def _value_pc(self):
     #     self.value2 = float(self.value) / 100
class Linkloving_ble_device(models.Model):
     _name = 'linkloving.ble.device'

     device_name = fields.Char()

     company_name = fields.Char()