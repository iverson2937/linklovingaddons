# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.depends('employee_ids')
    def is_employee(self):
        for em in self:
            if em.employee_ids:
                em.employee = True

    employee = fields.Boolean(compute='is_employee', store=True)
    employee_ids = fields.One2many('hr.employee', 'address_home_id')
