# -*- coding: utf-8 -*-

from odoo import models, fields, api

WORK_ORDER_ISSUE_STATE_UNACCEPT = 0
WORK_ORDER_ISSUE_STATE_UNASSIGNED = 1
WORK_ORDER_ISSUE_STATE_PROCESS = 2
WORK_ORDER_ISSUE_STATE_CHECK = 3
WORK_ORDER_ISSUE_STATE_DONE = 9


class linkloving_work_order(models.Model):
    _name = 'linkloving.work.order'

    order_number = fields.Char()

    name = fields.Char()

    assign_uid = fields.Many2one('res.users')

    execute_uid = fields.Many2one('res.users')

    effective_department_ids = fields.Many2many('hr.department', 'linkloving_work_order_department_rel', 'work_order_id', 'department_id', 'Department id', ondelete='cascade')

    priority = fields.Integer()

    description = fields.Text()

    issue_state = fields.Selection([
        ('unaccept', '未指定受理人'),
        ('unassign ', '未指派'),
        ('process', '处理中'),
        ('check', '待审核'),
        ('done', '已完成')
    ], default='unaccept')

    assign_time = fields.Datetime()

    finish_time = fields.Datetime()

    attachments = fields.One2many(comodel_name="linkloving.work.order.image", inverse_name="work_order_id", string="工单图片",
                              required=False, )

    @api.model
    def create(self, vals):
        if not vals.get('order_number'):
            vals['order_number'] = self.env['ir.sequence'].next_by_code('work.order.number') or '/'
        return super(linkloving_work_order, self).create(vals)