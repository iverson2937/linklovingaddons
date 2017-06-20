# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

AVAILABLE_PRIORITIES = [
    ('0', 'badly'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
    ('5', 'top level'),
]


class project_issue(models.Model):
    _inherit = 'project.issue'

    version_id = fields.Many2one('project.issue.version', 'Version')

    legend_audit = fields.Char(related="stage_id.legend_audit", string='Kanban Audit Explanation', readonly=True)

    legend_close = fields.Char(related="stage_id.legend_close", string='Kanban Audit Explanation', readonly=True)

    legend_pending = fields.Char(related="stage_id.legend_pending", string='Kanban Audit Explanation', readonly=True)

    date_deadline = fields.Date(string=u'截止日期')
    planed_level = fields.Selection(AVAILABLE_PRIORITIES, string=u'计划星级')
    actual_level = fields.Selection(AVAILABLE_PRIORITIES, string=u'质量星级')


    @api.onchange("project_id")
    def on_change_project(self):
        if self.project_id and self.project_id.partner_id:
            return {
                'value': {'partner_id': self.project_id.partner_id.id, 'email_from': self.project_id.partner_id.email}}
        return {}
