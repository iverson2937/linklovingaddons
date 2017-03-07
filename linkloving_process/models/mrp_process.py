# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpProcess(models.Model):
    _name = 'mrp.process'
    name = fields.Char(string=u'名称')
    description = fields.Text(string=u'描述')
    unit_price = fields.Float(string=u'计件单价')
    hour_price = fields.Float(string=u'时薪')
    partner_id = fields.Many2one('res.partner', string=u'负责人')
