# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class MrpProcessAction(models.Model):
    _name = 'mrp.process.action'
    name = fields.Char(string='名称')
    process_id = fields.Many2one('mrp.process', string=u'工序')
    cost = fields.Float(string=u'成本', digits=dp.get_precision('Discount'))
    remark = fields.Char(string='备注')
    line_ids = fields.One2many('process.action.line', 'action_id')

    @api.model
    def unlink(self):
        if self.line_ids:
            raise UserError('已经在bom中使用，不可以删除')
        return super(MrpProcessAction, self).unlink()


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
            else:
                line.line_cost = 0
