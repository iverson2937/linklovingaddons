# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"
    source_mo_id = fields.Many2one('mrp.production')
    source_mo_ids = fields.One2many('mrp.production', 'mo_id')
