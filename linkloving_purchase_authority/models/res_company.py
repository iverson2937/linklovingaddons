# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import models, fields, api, _, SUPERUSER_ID


class Company(models.Model):
    _inherit = 'res.company'
    payment_apply_amount = fields.Float()
