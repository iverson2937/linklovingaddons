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
    hour_price = fields.Float(string=u'时薪')
    in_charge_id = fields.Many2one('res.partner')

    @api.onchange('bom_id')
    def on_change_bom_id(self):
        self.process_id = self.bom_id.process_id
        self.unit_price = self.process_id.unit_price
        self.mo_type = self.bom_id.mo_type
        self.hour_price = self.bom_id.hour_price
        self.in_charge_id = self.process_id.partner_id
