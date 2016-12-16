# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountEmployeeRegisterPaymentWizard(models.TransientModel):
    _name = "account.employee.payable.wizard"
    _description = "Hr Expense Register Payment wizard"


