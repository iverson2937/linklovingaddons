# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class MrpProduction(models.Model):
    _inherit = 'mrp.bom'
    process_id = fields.Many2one('mrp.process', string=u'工序')
    unit_price = fields.Float(string=u'计件单价')
    mo_type = fields.Selection([
        ('unit', u'Base on Unit'),
        ('time', u'Base on Time'),
    ], default='unit')
    cycle_time = fields.Integer(string=u'Cycle Time')
    cycle_time_time_unit = fields.Many2one('product.uom')

    @api.depends('cost', 'hour_price')
    def _get_product_cost(self):
        self.cost = (float(self.cycle_time) / 3600) * self.hour_price

    cost = fields.Monetary(string=u'Cost', compute=_get_product_cost, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    hour_price = fields.Float(string=u'时薪')

    @api.onchange('process_id')
    def on_change_price(self):
        self.hour_price = self.process_id.hour_price
