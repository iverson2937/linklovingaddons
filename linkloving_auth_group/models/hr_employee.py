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

    #
    # @api.multi
    # def write(self, vals):
    #     res = super(HrEmployee, self).write(vals)
    #     groups = []
    #     for job in self.hr_job_ids:
    #         for group in job.groups_id:
    #             groups.append(group.id)
    #             self.env['res.users'].browse(self.user_id.id).write({
    #                 'groups_id': [(6, 0, groups)]
    #             })
    #     return res

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        groups = []
        for job in self.hr_job_ids:
            for group in job.groups_id:
                groups.append(group.id)
                self.env['res.users'].browse(self.user_id.id).write({
                    'groups_id': [(6, 0, groups)]
                })
        return res


