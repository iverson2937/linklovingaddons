# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class MrpProduction(models.Model):
    _inherit = 'mrp.bom'
    process_id = fields.Many2one('mrp.process')
    unit_price = fields.Float()

    mo_type = fields.Selection([
        ('unit', u'计件计价'),
        ('time', u'计时计价'),
    ], default='unit')
    cycle_time = fields.Integer(string=u'理论工时')

    @api.depends('cost', 'hour_price')
    def _get_product_cost(self):
        self.cost = (float(self.cycle_time) / 3600) * self.hour_price

    cost = fields.Monetary(string=u'成本', compute=_get_product_cost,currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    hour_price = fields.Float(string=u'时薪')
    @api.onchange('process_id')
    def on_change_price(self):
        self.hour_price = self.process_id.hour_price


