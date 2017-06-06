# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class linkloving_project(models.Model):
    _inherit = 'project.project'

    state = fields.Selection([('template', 'Template'),
                              ('draft', 'New'),
                              ('open', 'In Progress'),
                              ('cancelled', 'Cancelled'),
                              ('pending', 'Pending'),
                              ('close', 'Closed')],
                             'Status', copy=False, default='draft')
    issue_count = fields.Float()

    #
    # # TODO 计算项目耗时, 未实现
    # def onchange_partner_id(self, part=False):
    #     partner_obj = self.env['res.partner']
    #     val = {}
    #     if not part:
    #         return {'value': val}
    #     if 'pricelist_id' in self.fields_get():
    #         pricelist = partner_obj.read(part, ['property_product_pricelist'])
    #         pricelist_id = pricelist.get('property_product_pricelist', False) and \
    #                        pricelist.get('property_product_pricelist')[0] or False
    #         val['pricelist_id'] = pricelist_id
    #     return {'value': val}

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        val = {}
        if not self.partner_id:
            return {'value': val}
        partner_id = self.partner_id
        pricelist_id = partner_id.property_product_pricelist
        self.pricelist_id = pricelist_id

    # def _get_project_and_children(self,ids):
    #     """ retrieve all children projects of project ids;
    #         return a dictionary mapping each project to its parent project (or None)
    #     """
    #
    #     res = dict.fromkeys(ids, None)
    #     # while self._ids:
    #     #     self._cr.execute("""
    #     #         SELECT project.id, parent.id
    #     #         FROM project_project project, project_project parent, account_analytic_account account
    #     #         WHERE project.analytic_account_id = account.id
    #     #         AND parent.id IN %s
    #     #         """, (tuple(ids),))
    #     #     dic = dict(self._cr.fetchall())
    #     #     res.update(dic)
    #     #     ids = dic.keys()
    #     return res
    #
    # def _progress_rate(self):
    #     child_parent = self._get_project_and_children(self._ids)
    #     # compute planned_hours, total_hours, effective_hours specific to each project
    #     self._cr.execute("""
    #         SELECT project_id, COALESCE(SUM(planned_hours), 0.0),
    #             COALESCE(SUM(total_hours), 0.0), COALESCE(SUM(effective_hours), 0.0)
    #         FROM project_task
    #         LEFT JOIN project_task_type ON project_task.stage_id = project_task_type.id
    #         WHERE project_task.project_id IN %s AND project_task_type.fold = False
    #         GROUP BY project_id
    #         """, (tuple(child_parent.keys()),))
    #     # aggregate results into res
    #     res = dict([(id, {'planned_hours': 0.0, 'total_hours': 0.0, 'effective_hours': 0.0}) for id in self._ids])
    #     for id, planned, total, effective in self._cr.fetchall():
    #         # add the values specific to id to all parent projects of id in the result
    #         while id:
    #             if id in self:
    #                 res[id]['planned_hours'] += planned
    #                 res[id]['total_hours'] += total
    #                 res[id]['effective_hours'] += effective
    #             id = child_parent[id]
    #     # compute progress rates
    #     for id in self:
    #         if res[id]['total_hours']:
    #             res[id]['progress_rate'] = round(100.0 * res[id]['effective_hours'] / res[id]['total_hours'], 2)
    #         else:
    #             res[id]['progress_rate'] = 0.0
    #     return res

    # TODO 计算项目耗时, 未实现
    def _progress_rate(self):
        return 5.5

    planned_hours = fields.Float(compute=_progress_rate)

    # TODO 未实现
    effective_hours = fields.Float()

    # TODO 未实现
    parent_id = fields.Integer()

    # TODO 未实现
    progress_rate = fields.Float(compute=_progress_rate)

    # TODO 未实现
    total_hours = fields.Float(compute=_progress_rate)

    @api.depends('use_tasks', 'use_issues')
    def on_change_use_tasks_or_issues(self):
        values = {}
        if self.use_tasks and not self.use_issues:
            values['alias_model'] = 'project.task'
        elif not self.use_tasks and self.use_issues:
            values['alias_model'] = 'project.issue'
        return {'value': values}


class linkloving_project_task(models.Model):
    _inherit = 'project.task'

    _order = "priority desc, sequence, date_start, name, id"

    # TODO 计算项目耗时, 未实现
    def _progress_rate(self):
        return 5.5

    # TODO 未实现
    def _hours_get(self):
        return 5.0

    reviewer_id = fields.Many2one('res.users', string='Reviewer', select=True, track_visibility='onchange',
                                  default=lambda self: self.env.user)

    parent_ids = fields.Many2many('project.task', 'project_task_parent_rel', 'task_id', 'parent_id', 'Parent Tasks')

    child_ids = fields.Many2many('project.task', 'project_task_parent_rel', 'parent_id', 'task_id', 'Delegated Tasks')

    work_ids = fields.One2many('project.task.work', 'task_id', 'Work done')

    # TODO 未实现
    effective_hours = fields.Float(compute=_hours_get, string='Hours Spent')

    # TODO 未实现
    progress = fields.Float(compute=_hours_get, string='Working Time Progress (%)')

    # TODO 未实现
    total_hours = fields.Float(compute=_hours_get, string='Total')

    delegated_user_id = fields.Many2one('res.users', string='Delegated To', related='child_ids.user_id')

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


class project_category(models.Model):
    """ Category of project's task (or issue) """
    _name = "project.category"
    _description = "Category of project's task, issue, ..."

    name = fields.Char(string='Name', required=True, translate=True)


class project_work(models.Model):
    _name = "project.task.work"
    _description = "Project Task Work"


    _order = "date desc"

    name = fields.Char('Work summary')
    date = fields.Datetime('Date', select="1", default=lambda *a: fields.Datetime.now())
    task_id = fields.Many2one('project.task', 'Task', ondelete='cascade', required=True, select="1")
    hours = fields.Float('Time Spent')
    user_id = fields.Many2one('res.users', 'Done by', required=True, select="1", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', related='task_id.company_id', store=True, readonly=True)

    def create(self, vals):
        if 'hours' in vals and (not vals['hours']):
            vals['hours'] = 0.00
        if 'task_id' in vals:
            self._cr.execute('update project_task set remaining_hours=remaining_hours - %s where id=%s',
                             (vals.get('hours', 0.0), vals['task_id']))
            self.env['project.task'].invalidate_cache(['remaining_hours'], [vals['task_id']])
        return super(project_work, self).create(vals)

    def write(self, vals):
        if 'hours' in vals and (not vals['hours']):
            vals['hours'] = 0.00
        if 'hours' in vals:
            task_obj = self.pool.get('project.task')
            for work in self:
                self._cr.execute('update project_task set remaining_hours=remaining_hours - %s + (%s) where id=%s',
                                 (vals.get('hours', 0.0), work.hours, work.task_id.id))
                task_obj.invalidate_cache(['remaining_hours'], [work.task_id.id])
        return super(project_work, self).write(vals)

    def unlink(self):
        task_obj = self.pool.get('project.task')
        for work in self:
            self._cr.execute('update project_task set remaining_hours=remaining_hours + %s where id=%s',
                             (work.hours, work.task_id.id))
            task_obj.invalidate_cache(['remaining_hours'], [work.task_id.id])
        return super(project_work, self).unlink()
