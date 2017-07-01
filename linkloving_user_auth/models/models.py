# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmployeeExtend(models.Model):
    _inherit = 'hr.employee'

    card_num = fields.Char(string=u"NFC卡号")