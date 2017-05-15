# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def document_load(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'document_manage',
            'product_id': self.id
        }

