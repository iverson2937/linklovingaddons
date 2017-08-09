# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpProcess(models.Model):
    _inherit = 'mrp.process'
    is_multi_output = fields.Boolean(string=u'是否为多产出')
    is_random_output=fields.Boolean(string=u'是否随机产出')
