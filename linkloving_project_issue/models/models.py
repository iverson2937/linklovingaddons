# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class linkloving_project_issue(models.Model):
#     _name = 'linkloving_project_issue.linkloving_project_issue'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100