# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    legend_audit = fields.Char(
        string='Kanban Audit Explanation', translate=True,
        help='Override the default value displayed for the done state for kanban selection, when the task or issue is in that stage.')

    legend_close = fields.Char(
        string='Kanban Close Explanation', translate=True,
        help='Override the default value displayed for the done state for kanban selection, when the task or issue is in that stage.')

    legend_pending = fields.Char(
        string='Kanban Pending Explanation', translate=True,
        help='Override the default value displayed for the done state for kanban selection, when the task or issue is in that stage.')
