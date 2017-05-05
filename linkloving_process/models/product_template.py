# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import datetime
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    process_id = fields.Many2one('mrp.process', compute="get_process_id", store=True)

    @api.depends('bom_ids.process_id')
    def get_process_id(self):
        for product in self:
            if product.bom_ids:
                product.process_id = self.bom_ids[0].process_id.id
