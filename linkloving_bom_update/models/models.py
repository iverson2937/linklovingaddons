# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class linkloving_bom_update(models.Model):
#     _name = 'linkloving_bom_update.linkloving_bom_update'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100