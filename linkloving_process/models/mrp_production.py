# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    process_id = fields.Many2one('mrp.process', string=u'Process')
    unit_price = fields.Float()
    mo_type = fields.Selection([
        ('unit', _('Base on Unit')),
        ('time', _('Base on Time')),
    ], default='unit')
    hour_price = fields.Float(string=u'Price Per Hour')
    in_charge_id = fields.Many2one('res.partner')
    product_qty = fields.Float(
        _('Quantity To Produce'),
        default=1.0, digits=dp.get_precision('Payroll'),
        readonly=True, required=True,
        states={'confirmed': [('readonly', False)]})

    @api.onchange('bom_id')
    def on_change_bom_id(self):
        self.process_id = self.bom_id.process_id
        self.unit_price = self.process_id.unit_price
        self.mo_type = self.bom_id.mo_type
        self.hour_price = self.bom_id.hour_price
        self.in_charge_id = self.process_id.partner_id
