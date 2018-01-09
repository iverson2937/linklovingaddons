# -*- coding: utf-8 -*-

from odoo import models, fields


class linkloving_work_order_image(models.Model):
    _name = 'linkloving.work.order.image'

    work_order_image = fields.Binary(u"工单图片")

    work_order_id = fields.Many2one("linkloving.work.order", ondelete='cascade')
