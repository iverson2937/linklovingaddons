# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ReportProjectTaskUser(models.Model):
    _inherit = 'report.project.task.user'

    state = fields.Selection([
        ('normal', 'In Progress'),
        ('blocked', 'Blocked'),
        ('audit', u'待审核'),
        ('close', u'关闭'),
        ('pending', u'暂停'),
        ('done', 'Ready for next stage')
    ], string='Kanban State', readonly=True)