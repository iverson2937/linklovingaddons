# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    process_id = fields.Many2one('mrp.process')
    is_in_charge = fields.Boolean(string='Is In Charge')


