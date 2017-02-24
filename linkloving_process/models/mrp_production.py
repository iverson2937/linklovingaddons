# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    process_id = fields.Many2one('mrp.process', string=u'工序')
    unit_price = fields.Float()
    mo_type = fields.Selection([
        ('unit', u'计件计价'),
        ('time', u'计时计价'),
    ], default='unit')

    @api.onchange('bom_id')
    def on_change_bom_id(self):
        self.process_id = self.bom_id.process_id
        if self.mo_type == 'unit':
            self.unit_price = self.process_id.unit_price
        self.mo_type = self.bom_id.mo_type