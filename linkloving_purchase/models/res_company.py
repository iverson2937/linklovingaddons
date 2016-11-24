# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    """
    采购单
    """
    _inherit = 'res.company'
    purchase_note = fields.Text(string='Default Terms and Conditions', translate=True)
