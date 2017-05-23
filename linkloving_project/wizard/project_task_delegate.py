# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from lxml import etree

from odoo import models, fields, api, tools, _


# class project_task_delegate(osv.osv_memory):
class project_task_delegate(models.TransientModel):
    _name = 'project.task.delegate'
    _description = 'Task Delegate'

    name = fields.Char('Delegated Title', required=True, help="New title of the task delegated to the user")
    prefix = fields.Char('Your Task Title', help="Title for your validation task")
    project_id = fields.Many2one('project.project', 'Project', help="User you want to delegate this task to")
    user_id = fields.Many2one('res.users', 'Assign To', required=True, help="User you want to delegate this task to")
    new_task_description = fields.Text('New Task Description',
                                       help="Reinclude the description of the task in the task of the user")
    planned_hours = fields.Float('Planned Hours', help="Estimated time to close this task by the delegated user")
    planned_hours_me = fields.Float('Hours to Validate',
                                    help="Estimated time for you to validate the work done by the user to whom you delegate this task",
                                    default='1.0')
    state = fields.Selection([('pending', 'Pending'), ('done', 'Done'), ], 'Validation State',
                             help="New state of your own task. Pending will be reopened automatically when the delegated task is closed",
                             default='pending')


# def onchange_project_id(self, project_id=False, context=None):
#     project_project = self.pool.get('project.project')
#     if not project_id:
#         return {'value': {'user_id': False}}
#     project = project_project.browse(project_id, context=context)
#     return {'value': {'user_id': project.user_id and project.user_id.id or False}}
    @api.onchange('project_id')
    def onchange_project_id(self):
        if not self.project_id:
            self.user_id = False
        else:
            self.user_id = self.project_id.user_id and self.project_id.user_id.id or False


# def default_get(self):
#     """
#     This function gets default values
#     """
#     res = super(project_task_delegate, self).default_get(cr, uid, fields, context=context)
#     if context is None:
#         context = {}
#     record_id = context and context.get('active_id', False) or False
#     if not record_id:
#         return res
#     task_pool = self.pool.get('project.task')
#     task = task_pool.browse(cr, uid, record_id, context=context)
#     task_name = tools.ustr(task.name)
#
#     if 'project_id' in fields:
#         res['project_id'] = int(task.project_id.id) if task.project_id else False
#
#     if 'name' in fields:
#         if task_name.startswith(_('CHECK: ')):
#             newname = tools.ustr(task_name).replace(_('CHECK: '), '')
#         else:
#             newname = tools.ustr(task_name or '')
#         res['name'] = newname
#     if 'planned_hours' in fields:
#         res['planned_hours'] = task.remaining_hours or 0.0
#     if 'prefix' in fields:
#         if task_name.startswith(_('CHECK: ')):
#             newname = tools.ustr(task_name).replace(_('CHECK: '), '')
#         else:
#             newname = tools.ustr(task_name or '')
#         prefix = _('CHECK: %s') % newname
#         res['prefix'] = prefix
#     if 'new_task_description' in fields:
#         res['new_task_description'] = task.description
#     return res
    @api.model
    def default_get(self, fields):
        """
        This function gets default values
        """
        res = super(project_task_delegate, self).default_get(fields)
        context = self._context
        record_id = context and context.get('active_id', False) or False
        if not record_id:
            return res
        task = self.env['project.task'].browse(record_id)
        task_name = tools.ustr(task.name)

        if 'project_id' in fields:
            res['project_id'] = int(task.project_id.id) if task.project_id else False

        if 'name' in fields:
            if task_name.startswith(_('CHECK: ')):
                newname = tools.ustr(task_name).replace(_('CHECK: '), '')
            else:
                newname = tools.ustr(task_name or '')
            res['name'] = newname
        if 'planned_hours' in fields:
            res['planned_hours'] = task.remaining_hours or 0.0
        if 'prefix' in fields:
            if task_name.startswith(_('CHECK: ')):
                newname = tools.ustr(task_name).replace(_('CHECK: '), '')
            else:
                newname = tools.ustr(task_name or '')
            prefix = _('CHECK: %s') % newname
            res['prefix'] = prefix
        if 'new_task_description' in fields:
            res['new_task_description'] = task.description
        return res


#
# def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
#     res = super(project_task_delegate, self).fields_view_get(cr, uid, view_id, view_type, context=context,
#                                                              toolbar=toolbar, submenu=submenu)
#     users_pool = self.pool.get('res.users')
#     obj_tm = users_pool.browse(cr, uid, uid, context=context).company_id.project_time_mode_id
#     tm = obj_tm and obj_tm.name or 'Hours'
#     if tm in ['Hours', 'Hour']:
#         return res
#
#     eview = etree.fromstring(res['arch'])
#
#     def _check_rec(eview):
#         if eview.attrib.get('widget', '') == 'float_time':
#             eview.set('widget', 'float')
#         for child in eview:
#             _check_rec(child)
#         return True
#
#     _check_rec(eview)
#     res['arch'] = etree.tostring(eview)
#     for field in res['fields']:
#         if 'Hours' in res['fields'][field]['string']:
#             res['fields'][field]['string'] = res['fields'][field]['string'].replace('Hours', tm)
#     return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(project_task_delegate, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                 toolbar=toolbar, submenu=submenu)

        users_pool = self.env['res.users']
        obj_tm = self.env.user.company_id.project_time_mode_id
        tm = obj_tm and obj_tm.name or 'Hours'
        if tm in ['Hours', 'Hour']:
            return res

        eview = etree.fromstring(res['arch'])

        def _check_rec(eview):
            if eview.attrib.get('widget', '') == 'float_time':
                eview.set('widget', 'float')
            for child in eview:
                _check_rec(child)
            return True

        _check_rec(eview)
        res['arch'] = etree.tostring(eview)
        for field in res['fields']:
            if 'Hours' in res['fields'][field]['string']:
                res['fields'][field]['string'] = res['fields'][field]['string'].replace('Hours', tm)
        return res


# def delegate(self, cr, uid, ids, context=None):
#     if context is None:
#         context = {}
#     task_id = context.get('active_id', False)
#     task_pool = self.pool.get('project.task')
#     delegate_data = self.read(cr, uid, ids, context=context)[0]
#     delegated_tasks = task_pool.do_delegate(cr, uid, [task_id], delegate_data, context=context)
#     models_data = self.pool.get('ir.model.data')
#
#     action_model, action_id = models_data.get_object_reference(cr, uid, 'project', 'action_view_task')
#     view_model, task_view_form_id = models_data.get_object_reference(cr, uid, 'project', 'view_task_form2')
#     view_model, task_view_tree_id = models_data.get_object_reference(cr, uid, 'project', 'view_task_tree2')
#     action = self.pool[action_model].read(cr, uid, [action_id], context=context)[0]
#     action['res_id'] = delegated_tasks[task_id]
#     action['view_id'] = False
#     action['views'] = [(task_view_form_id, 'form'), (task_view_tree_id, 'tree')]
#     action['help'] = False
#     return action  # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

    def delegate(self):
        if self._context is None:
            self._context = {}
        task_id = self._context.get('active_id', False)
        task_pool = self.env['project.task']
        delegate_data = self.read()[0]
        delegated_tasks = task_pool.do_delegate([task_id], delegate_data)
        models_data = self.env['ir.model.data']

        action_model, action_id = models_data.get_object_reference('project', 'action_view_task')
        view_model, task_view_form_id = models_data.get_object_reference('project', 'view_task_form2')
        view_model, task_view_tree_id = models_data.get_object_reference('project', 'view_task_tree2')
        action = self.env[action_model].browse(action_id)
        action['res_id'] = delegated_tasks[task_id]
        action['view_id'] = False
        action['views'] = [(task_view_form_id, 'form'), (task_view_tree_id, 'tree')]
        action['help'] = False
        return action  # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
