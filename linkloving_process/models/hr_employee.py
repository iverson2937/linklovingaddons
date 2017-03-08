# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    is_in_charge = fields.Boolean(related='address_home_id.is_in_charge')
