# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from itertools import chain, repeat
from collections import defaultdict, MutableMapping, OrderedDict

#
# Functions for manipulating boolean and selection pseudo-fields
#
from odoo.addons.base.res.res_users import parse_m2m
from odoo.exceptions import UserError
from odoo.tools import partition


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hr_job_ids = fields.Many2many('hr.job', 'hr_job_hr_employee_rel', 'job_id', 'employee_id')

    # @api.multi
    # @api.onchange('hr_job_ids')
    # def _on_change_job_ids(self):
    #     for emp in self:
    #         if not emp.user_id:
    #             raise UserError(u'请给员工设置相关用户')
    #         groups = []
    #         for job in emp.hr_job_ids:
    #             for group in job.groups_id:
    #                 groups.append(group.id)
    #         print groups, 'dddddd'
    #         self.env['res.users'].browse(emp.user_id.id).write({
    #             'groups_id': [(6, 0, groups)]
    #         })
    @api.multi
    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        groups = []
        for job in self.hr_job_ids:
            for group in job.groups_id:
                groups.append(group.id)
                self.env['res.users'].browse(self.user_id.id).write({
                    'groups_id': [(6, 0, groups)]
                })

        return res

# class ResUser(models.Model):
#     _inherit = 'res.users'
#     @api.multi
#     def write(self, vals):
#         print vals, 'dddddddddddddddsssssssssssssssssss'
#         return super(ResUser, self).write(vals)
#
#     def update_groups(self,groups):
#         self.write({'groups_id':[(6, 0, groups)]})
