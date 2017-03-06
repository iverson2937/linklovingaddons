# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class MrpProduction(models.Model):
    _inherit = 'mrp.bom'
    process_id = fields.Many2one('mrp.process')
    unit_price = fields.Float()
    mo_type = fields.Selection([
        ('unit', u'Base on Unit'),
        ('time', u'Base on Time'),
    ], default='unit')
