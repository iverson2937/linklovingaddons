# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    def is_employee(self):
        if self.employee_ids:
            self.employee = True

    employee = fields.Boolean(compute='is_employee',store=True)
    employee_ids = fields.One2many('hr.employee', 'address_home_id')
