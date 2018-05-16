# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.department'

    allow_amount = fields.Float(string='允许最大金额')

    def get_to_approve_id(self, employee_id, total_amount):
        state = ''
        to_approve_id = False
        if employee_id == self.manager_id:
            # 报销金额小于部门允许金额直接通过
            if not self.parent_id or (
                    self.allow_amount and total_amount < self.allow_amount):
                state = 'approve'
            else:
                if not self.parent_id.manager_id:
                    raise UserError(u'上级部门未设置审核人')
                to_approve_id = self.parent_id.manager_id.user_id.id
        else:
            if not self.manager_id:
                raise UserError(u'请设置部门审核人')
            to_approve_id = self.sudo().manager_id.user_id.id
        return state, to_approve_id
