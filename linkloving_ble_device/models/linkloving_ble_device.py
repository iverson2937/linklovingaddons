# -*- coding: utf-8 -*-

from odoo import models, fields, api


class linkloving_ble_device(models.Model):
    _name = 'linkloving.ble.device'

    device_name = fields.Char()

    company_name = fields.Char()