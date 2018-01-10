# -*- coding: utf-8 -*-

from odoo import models, fields

WORK_ORDER_RECORD_STATE_REPLY = 1
WORK_ORDER_RECORD_STATE_CREATE = 101
WORK_ORDER_RECORD_STATE_ASSIGN = 102
WORK_ORDER_RECORD_STATE_AUDIT = 103
WORK_ORDER_RECORD_STATE_REJECT = 104
WORK_ORDER_RECORD_STATE_FINISH = 105


class linkloving_work_order_record(models.Model):
    _name = 'linkloving.work.order.record'

    order_number = fields.Char()

    name = fields.Char()

    work_order_id = fields.Many2one('linkloving.work.order')

    record_type = fields.Integer(default=WORK_ORDER_RECORD_STATE_REPLY)

    record_type = fields.Selection([
        ('reply', '回复'),
        ('create ', '创建'),
        ('assign', '指派'),
        ('check', '审核'),
        ('reject', '驳回'),
        ('finish', '完成')
    ], default='reply')

    reply_uid = fields.Many2one("res.users")

    content = fields.Char()

