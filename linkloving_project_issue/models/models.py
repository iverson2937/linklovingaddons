# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectIssue(models.Model):
    _inherit = 'project.issue'
    version_id = fields.Many2one('project.issue.version')
    categ_ids = fields.Many2many('project.category')
    message_summary = fields.Text()
    project_escalation_id = fields.Many2one('project.project', 'Project Escalation',
                                            help='If any issue is escalated from the current Project, it will be listed under the project selected here.',
                                            states={'close': [('readonly', True)], 'cancelled': [('readonly', True)]})


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.depends('use_tasks', 'use_issues')
    def on_change_use_tasks_or_issues(self):
        values = {}
        if self.use_tasks and not self.use_issues:
            values['alias_model'] = 'project.task'
        elif not self.use_tasks and self.use_issues:
            values['alias_model'] = 'project.issue'
        return {'value': values}
