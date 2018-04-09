# -*- coding: utf-8 -*-

from odoo import models, fields


class linkloving_work_order_record_image(models.Model):
    _name = 'linkloving.work.order.record.image'

    work_order_record_image = fields.Binary(u"工单回复图片")

    work_order_record_id = fields.Many2one("linkloving.work.order.record", ondelete='cascade')
