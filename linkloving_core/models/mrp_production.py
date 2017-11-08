# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api
from models import MO_STATE
import uuid

from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _compute_on_produce_qty(self):
        for stock_move in self:
            finished_product = sum(
                move.product_uom_qty for move in stock_move.move_finished_ids.filtered(lambda x: x.state == 'done'))
            stock_move.on_produce_qty = stock_move.product_qty - finished_product

    on_produce_qty = fields.Float(compute=_compute_on_produce_qty)

    @api.model
    def delete_mos(self, mo_ids):
        for mo_id in mo_ids:
            mo = self.browse(mo_id)
            if mo.state in ['draft', 'confirmed', 'waiting_material']:
                mo.action_cancel()
                mo.unlink()
            else:
                raise UserError('只有未生产的MO才可以删除')
        return True


