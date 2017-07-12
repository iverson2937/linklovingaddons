# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class linkloving_project(models.Model):
    _inherit = 'project.project'

    project_escalation_id = fields.Many2one('project.project', 'Project Escalation',
                                            help='If any issue is escalated from the current Project, it will be listed under the project selected here.',
                                            states={'close': [('readonly', True)],
                                                    'cancelled': [('readonly', True)]})
    members = fields.Many2many('res.users', 'project_user_rel', 'project_id', 'uid', 'Project Members',
                               help="Project's members are users who can have an access to the tasks related to this project.",
                               states={'close': [('readonly', True)], 'cancelled': [('readonly', True)]})

    currency_id = fields.Many2one('res.currency', string='Currency')

    def _check_escalation(self):
        for project in self:
            if project.project_escalation_id:
                if project.project_escalation_id.id == project.id:
                    return False
            return True

    _constraints = [
        (_check_escalation, 'Error! You cannot assign escalation to the same project!', ['project_escalation_id'])
    ]

    state = fields.Selection([('template', 'Template'),
                              ('draft', 'New'),
                              ('open', 'In Progress'),
                              ('cancelled', 'Cancelled'),
                              ('pending', 'Pending'),
                              ('close', 'Closed')],
                             'Status', copy=False, default='draft')


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

    def _compute_task_count(self):
        for project in self:
            count = 0
            for task_id in project.task_ids:
                if not task_id.parent_ids:
                    count += 1
            project.task_count = count

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
    progress = fields.Float(string=u'完成进度')
    user_id = fields.Many2one('res.users', 'Done by', required=True, select="1", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', related='task_id.company_id', store=True, readonly=True)

    @api.model
    def create(self, vals):
        if 'hours' in vals and (not vals['hours']):
            vals['hours'] = 0.00
        if 'task_id' in vals:
            self._cr.execute('update project_task set remaining_hours=remaining_hours - %s where id=%s',
                             (vals.get('hours', 0.0), vals['task_id']))
            self.env['project.task'].invalidate_cache(['remaining_hours'], [vals['task_id']])

        res = super(project_work, self).create(vals)

        res.task_id.task_progress = res.progress
        if res.progress == 100:
            res.task_id.kanban_state = 'audit'
        else:
            res.task_id.kanban_state = 'normal'

        return res



    @api.multi
    def write(self, vals):
        if 'progress' in vals:
            self.task_id.progress=vals['progress']
            if vals['progress'] == 100:
                self.task_id.kanban_state = 'audit'
        # if 'hours' in vals and (not vals['hours']):
        #     vals['hours'] = 0.00
        # if 'hours' in vals:
        #     task_obj = self.env['project.task']
        #     for work in self:
        #         self._cr.execute('update project_task set remaining_hours=remaining_hours - %s + (%s) where id=%s',
        #                          (vals.get('hours', 0.0), work.hours, work.task_id.id))
        #         task_obj.invalidate_cache(['remaining_hours'], [work.task_id.id])
        return super(project_work, self).write(vals)

    @api.multi
    def unlink(self):
        task_obj = self.env['project.task']
        for work in self:
            self._cr.execute('update project_task set remaining_hours=remaining_hours + %s where id=%s',
                             (work.hours, work.task_id.id))
            task_obj.invalidate_cache(['remaining_hours'], [work.task_id.id])
        return super(project_work, self).unlink()
