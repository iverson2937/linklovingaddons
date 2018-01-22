# -*- coding: utf-8 -*-

from odoo import models, fields


class linkloving_work_order_tag(models.Model):
    _name = 'linkloving.work.order.tag'

    name = fields.Char()
