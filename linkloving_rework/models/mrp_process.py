# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import datetime
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpProcess(models.Model):
    _inherit = 'mrp.process'
    is_rework = fields.Boolean(string='是否为重工')
