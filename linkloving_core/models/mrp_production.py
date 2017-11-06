# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api
from models import MO_STATE
import uuid

from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _compute_on_produce_qty(self):
        finished_product = sum(
            move.product_uom_qty for move in self.move_finished_ids.filtered(lambda x: x.state == 'done'))
        self.on_produce_qty = self.product_qty - finished_product

    on_produce_qty = fields.Float(compute=_compute_on_produce_qty)
