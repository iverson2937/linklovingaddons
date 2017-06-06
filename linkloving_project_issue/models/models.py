# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectIssue(models.Model):
    _inherit = 'project.issue'
    version_id = fields.Many2one('project.issue.version')
    categ_ids = fields.Many2many('project.category')
