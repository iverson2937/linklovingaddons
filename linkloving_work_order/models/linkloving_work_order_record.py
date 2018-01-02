# -*- coding: utf-8 -*-

from odoo import models, fields, api

class linkloving_work_order_record(models.Model):
    _name = 'linkloving.work.order.record'

    order_number = fields.Char()

    name = fields.Char()

    work_order_id = fields.Many2one('linkloving.work.order')

