# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class linkloving_custom_edit(models.Model):
#     _name = 'linkloving_custom_edit.linkloving_custom_edit'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
