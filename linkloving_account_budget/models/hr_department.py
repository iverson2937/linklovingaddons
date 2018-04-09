# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    has_budget = fields.Boolean(compute='_get_has_budget', store=True)
    budget_ids = fields.One2many('linkloving.account.budget', 'department_id')

    @api.multi
    @api.depends('budget_ids')
    def _get_has_budget(self):
        for d in self:
            if d.budget_ids:
                d.has_budget = True
            else:
                d.has_budget = False
