# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProjectIssueVersion(models.Model):
    _name = "project.issue.version"
    _order = "name desc"
    name = fields.Char('Version Number', required=True)
    active = fields.Boolean('Active', required=False, default=1)
