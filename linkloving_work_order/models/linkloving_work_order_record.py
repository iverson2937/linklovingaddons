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
    parent_id = fields.Many2one('linkloving.work.order.record')

    work_order_id = fields.Many2one('linkloving.work.order')

    record_type = fields.Integer(default=WORK_ORDER_RECORD_STATE_REPLY)

    record_type = fields.Selection([
        ('reply', '回复'),
        ('create ', '创建'),
        ('assign', '指派'),
        ('check', '审核'),
        ('reject', '驳回'),
        ('finish', '完成'),
        ('draft', '草稿')
    ], default='reply')

    isRead = fields.Boolean(default=False)

    reply_uid = fields.Many2one("res.users")

    content = fields.Char()

    reply_record_line_ids = fields.One2many('linkloving.work.order.record', 'parent_id')

    attachments = fields.One2many(comodel_name="linkloving.work.order.record.image",
                                  inverse_name="work_order_record_id",
                                  string="工单回复图片",
                                  required=False, )
