# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpProcessAction(models.Model):
    _name = 'mrp.process.action'
    name = fields.Char(string='名称')
    process_id = fields.Many2one('mrp.process', string=u'工序')
    cost = fields.Float(string=u'成本')
    speed = fields.Float(string=u'速度')
    time = fields.Float(string=u'时间')
    hour_price = fields.Float(string=u'时薪')


class MrpProcess(models.Model):
    _inherit = 'mrp.process'
    process_action_ids = fields.One2many('mrp.process.action', 'process_id')


class ProcessActionLine(models.Model):
    _name = 'process.action.line'
    bom_line_id = fields.Many2one('mrp.bom.line', on_delete="cascade")
    action_id = fields.Many2one('mrp.process.action', on_delete="restrict")
    rate = fields.Float(default=1)
    line_cost = fields.Float(compute='_get_line_cost')

    @api.multi
    def _get_line_cost(self):
        for line in self:
            line.line_cost = line.action_id.cost * line.rate
