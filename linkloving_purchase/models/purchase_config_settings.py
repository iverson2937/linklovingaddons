# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PurchaseConfiguration(models.TransientModel):
    _inherit = 'purchase.config.settings'
    purchase_note = fields.Text(related='company_id.purchase_note', string="Default Terms and Conditions *")
