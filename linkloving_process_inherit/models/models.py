# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpProcessAction(models.Model):
    _name = 'mrp.process.action'
    name = fields.Char(string='名称')
    process_id = fields.Many2one('mrp.process', string=u'工序')
    cost = fields.Float(string=u'成本')


class MrpProcess(models.Model):
    _inherit = 'mrp.process'
    process_action_ids = fields.One2many('mrp.process.action', 'process_id')
