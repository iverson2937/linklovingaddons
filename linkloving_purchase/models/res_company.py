# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'
    official_seal = fields.Binary(string=u'Official seal')
    purchase_note = fields.Text(string='Default Terms and Conditions', translate=True)
