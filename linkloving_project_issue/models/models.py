# -*- coding: utf-8 -*-

from odoo import models, fields, api


#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class linkloving_project_issue_version(models.Model):
    _name = "linkloving.project.issue.version"
    _order = "name desc"

    name = fields.Char('Version Number', required=True)
    active = fields.Boolean('Active', required=False, default=1)

class ProjectIssue(models.Model):
    _inherit = 'project.issue'
    version_id = fields.Many2one('project.issue.version')
