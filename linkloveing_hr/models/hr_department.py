# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.department'

    allow_amount = fields.Float(string='允许最大金额')

    def get_to_approve_id(self, employee_id, total_amount):
        state = ''
        if employee_id == self.manager_id:
            # 报销金额小于部门允许金额直接通过
            if not self.parent_id or (
                        self.allow_amount and total_amount < self.allow_amount):
                state = 'approve'
                return state, False
            else:
                if not self.parent_id.manager_id:
                    raise UserError(u'上级部门未设置审核人')
        else:
            if not self.manager_id:
                raise UserError(u'请设置部门审核人')
            return state, self.manager_id.user_id.id
