# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    mo_ids = fields.One2many('mrp.production', 'product_tmpl_id',
                             domain=[('state', 'in', ['draft', 'confirmed', 'waiting_material'])])

    @api.depends('mo_ids')
    def _compute_mo_ids(self):
        for product in self:
            if product.mo_ids:
                product.has_mo = True

    has_mo = fields.Boolean(compute=_compute_mo_ids, store=True)
