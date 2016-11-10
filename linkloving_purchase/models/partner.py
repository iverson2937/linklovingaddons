# -*- coding: utf-8 -*-
from odoo import models, fields, _


class Partner(models.Model):
    _inherit = 'res.partner'
    supplier_level = fields.Many2one('res.partner.level', string=_('Supplier Level'))


class Company(models.Model):
    _inherit = 'res.company'
    official_seal = fields.Binary(string='公司公章')
