# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpProcess(models.Model):
    _name = 'mrp.process'
    name = fields.Char(string=u'Name')
    description = fields.Text(string=u'Description')
    unit_price = fields.Float(string=u'Price Unit')
    partner_id = fields.Many2one('res.partner', string=u'Responsible By',
                                 domain="[('is_in_charge','=',True)]")
    hour_price = fields.Float(string=u'Price Per Hour')
