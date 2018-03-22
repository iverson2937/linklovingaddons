# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class MrpProcessAction(models.Model):
    _name = 'mrp.process.action'
    name = fields.Char(string='名称')
    process_id = fields.Many2one('mrp.process', string=u'工序')
    cost = fields.Float(string=u'成本', digits=dp.get_precision('Produce Price'))
    speed = fields.Float(string=u'速度(mm/s)')
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
            if line.action_id and line.action_id.cost:
                line.line_cost = line.action_id.cost * line.rate
            elif not line.action_id.cost and line.action_id.speed and line.action_id.hour_price:
                circle = line.bom_line_id.product_id.head_circle
                speed = line.action_id.speed
                hour_price = line.action_id.hour_price
                if line.bom_line_id.product_id.head_circle:
                    if speed:
                        line.line_cost = ((circle / speed) * hour_price / 3600) * line.rate
