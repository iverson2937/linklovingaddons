# -*- coding: utf-8 -*-
import json
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def bom_update(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'bom_update',
            'bom_id': self.bom_ids[0].id
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def bom_update(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'bom_update',
            'bom_id': self.product_tmpl_id.bom_ids[0].id
        }
