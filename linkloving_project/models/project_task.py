# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_is_zero

AVAILABLE_PRIORITIES = [
    ('0', 'badly'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
    ('5', 'top level'),
]


class linkloving_project_task(models.Model):
    _inherit = 'project.task'

    _order = "priority desc, sequence, date_start, name, id"

    # TODO 计算项目耗时, 未实现
    def _progress_rate(self):
        return 5.5

    def _hours_get(self):
        res = {}
        self._cr.execute(
            "SELECT task_id, COALESCE(SUM(hours),0) FROM project_task_work WHERE task_id IN %s GROUP BY task_id",
            (tuple(self._ids),))
        hours = dict(self._cr.fetchall())
        for task in self:
            res[task.id] = {'effective_hours': hours.get(task.id, 0.0),
                            'total_hours': (task.remaining_hours or 0.0) + hours.get(task.id, 0.0)}
            res[task.id]['delay_hours'] = res[task.id]['total_hours'] - task.planned_hours
            res[task.id]['progress'] = 0.0
            if not float_is_zero(res[task.id]['total_hours'], precision_digits=2):
                res[task.id]['progress'] = round(
                    min(100.0 * hours.get(task.id, 0.0) / res[task.id]['total_hours'], 99.99), 2)
        return res

    # def _get_top_task(self):
    #     for task in self:
    #         if task.parent_ids:
    #             for parent_id in task.parent_ids:
    #                 if not parent_id.parent_ids:
    #                     return parent_id.id
    #                 else:
    #                     parent_id._get_top_task()

    def _get_top_task_id(self):
        for task in self:
            if task.parent_ids:
                for parent_id in task.parent_ids:
                    if not parent_id.parent_ids:
                        task.top_task_id = parent_id.id
                    else:
                        parent_id._get_top_task_id()

    reviewer_id = fields.Many2one('res.users', string='Reviewer', select=True, track_visibility='onchange',
                                  default=lambda self: self.env.user)
    planed_level = fields.Selection(AVAILABLE_PRIORITIES, string=u'计划星级')
    actual_level = fields.Selection(AVAILABLE_PRIORITIES, string=u'质量星级')

    parent_ids = fields.Many2many('project.task', 'project_task_parent_rel', 'task_id', 'parent_id', 'Parent Tasks')
    child_ids = fields.Many2many('project.task', 'project_task_parent_rel', 'parent_id', 'task_id', 'Delegated Tasks')
    work_ids = fields.One2many('project.task.work', 'task_id', 'Work done')

    top_task_id = fields.Integer(compute=_get_top_task_id, string='Top Task ID', store=True)

    date_start = fields.Date(string='Starting Date',
                             default=fields.date.today(),
                             index=True, copy=False)
    date_end = fields.Date(string='Ending Date', index=True, copy=False)

    task_progress = fields.Float(string='Progress (%)')

    # TODO 未实现
    effective_hours = fields.Float(compute=_hours_get, string='Hours Spent')

    # TODO 未实现
    progress = fields.Float(compute=_hours_get, string='Working Time Progress (%)')

    # TODO 未实现
    total_hours = fields.Float(compute=_hours_get, string='Total')

    delegated_user_id = fields.Many2one('res.users', string='Delegated To', related='child_ids.user_id')

    legend_audit = fields.Char(related='stage_id.legend_audit', string='Kanban Audit Explanation', readonly=True)

    legend_close = fields.Char(related='stage_id.legend_close', string='Kanban Close Explanation', readonly=True)

    legend_pending = fields.Char(related='stage_id.legend_pending', string='Kanban Pending Explanation', readonly=True)

    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready for next stage'),
        ('audit', u'待审核'),
        ('close', u'关闭'),
        ('pending', u'暂停'),
        ('blocked', 'Blocked')
    ],
        string='Kanban State',
        default='normal',
        track_visibility='onchange',
        required=True, copy=False,
        help="A task's kanban state indicates special situations affecting it:\n"
             " * Normal is the default situation\n"
             " * Blocked indicates something is preventing the progress of this task\n"
             " * Ready for next stage indicates the task is ready to be pulled to the next stage")

    @api.multi
    def do_delegate(self, task_ids, delegate_data=None):
        """
        Delegate Task to another users.
        """
        if delegate_data is None:
            delegate_data = {}
        assert delegate_data['user_id'], _("Delegated User should be specified")
        delegated_tasks = {}
        for task_id in task_ids:
            task = self.env['project.task'].browse(task_id)
            delegated_task_id = task.copy({
                'name': delegate_data['name'],
                'project_id': delegate_data['project_id'] and delegate_data['project_id'][0] or False,
                'stage_id': delegate_data.get('stage_id') and delegate_data.get('stage_id')[0] or False,
                'user_id': delegate_data['user_id'] and delegate_data['user_id'][0] or False,
                'planned_hours': delegate_data['planned_hours'] or 0.0,
                'parent_ids': [(6, 0, [task.id])],
                'description': delegate_data['new_task_description'] or '',
                'child_ids': [],
                'work_ids': []
            })
            self._delegate_task_attachments(task.id, delegated_task_id)
            newname = delegate_data['prefix'] or ''
            task.write({
                'remaining_hours': delegate_data['planned_hours_me'],
                'planned_hours': delegate_data['planned_hours_me'] + (task.effective_hours or 0.0),
                'name': newname,
            })
            delegated_tasks[task.id] = delegated_task_id
        return delegated_tasks

    def _delegate_task_attachments(self, task_id, delegated_task_id):
        attachment = self.env['ir.attachment']
        attachment_ids = attachment.search([('res_model', '=', self._name), ('res_id', '=', task_id)])
        new_attachment_ids = []
        for attachment_id in attachment_ids:
            new_attachment_ids.append(attachment.copy(attachment_id, default={'res_id': delegated_task_id}))
        return new_attachment_ids

    @api.onchange("planned_hours", "effective_hours")
    def onchange_planned(self):
        return {'value': {'remaining_hours': self.planned_hours - self.effective_hours}}

    @api.onchange('user_id')
    def onchange_user_id(self):
        vals = {}
        if self.user_id:
            vals['date_start'] = fields.datetime.now()
        return {'value': vals}

    def _get_child_top_task(self, task_id):
        if self.child_ids:
            for child in self.child_ids:
                if child.child_ids:
                    child._get_child_top_task(task_id)
                    # child.top_task_id = task_id
                else:
                    child.top_task_id = task_id
        else:
            self.top_task_id = 0

    @api.model
    def create(self, vals):
        res = super(linkloving_project_task, self).create(vals)

        if not res.parent_ids:
            res.top_task_id = res.id
        else:
            res._get_top_task_id()

        return res

    @api.multi
    def write(self, vals):
        res = super(linkloving_project_task, self).write(vals)

        if 'date_end' in vals:
            self._change_parents_date_end()

        if 'child_ids' in vals:
            self._get_child_top_task(self.id)
            child_ids = self.resolve_2many_commands('child_ids', vals.get('child_ids'))
            for child in child_ids:
                date_ends = []
                if child.get('date_end'):
                    date_ends.append(child.get('date_end'))
                if date_ends:
                    new_date_end = max(date_ends)
                    if self.date_end < new_date_end:
                        self.date_end = new_date_end
            self._change_parents_date_end()
        return res

    def _change_parents_date_end(self):
        if self.parent_ids:
            for parent_id in self.parent_ids:
                end = max(parent_id.child_ids.mapped('date_end'))
                if parent_id.date_end < end:
                    parent_id.date_end = end
                    parent_id._change_parents_date_end()
