# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.department'

    allow_amount = fields.Float(string='允许最大金额')

    def get_to_approve_department(self, employee_id):
        if self and not self.manager_id:
            raise UserError('请联系管理员设置%s部门负责人' % self.name)
        if self.manager_id == employee_id:
            if not self.parent_id:
                return False
            return self.parent_id.get_to_approve_department(employee_id)
        else:
            return self.id
