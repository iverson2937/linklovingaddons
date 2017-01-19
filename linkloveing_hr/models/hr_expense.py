# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    department_id = fields.Many2one('hr.department', string=u'部门')

    @api.depends('employee_id')
    def onchange_employee_id(self):
        self.department_id = self.employee_id.department_id



