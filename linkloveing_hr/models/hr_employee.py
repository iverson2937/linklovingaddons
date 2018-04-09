# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.addons import decimal_precision as dp


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    payment_ids = fields.One2many('account.employee.payment', 'employee_id')
    signature = fields.Binary(string=u'签名')
    purchase_signature = fields.Binary(string='采购签名')
    manager_department_ids = fields.One2many('hr.department', 'manager_id')

    @api.multi
    def _get_pre_payment_reminding(self):
        for employee in self:
            employee.pre_payment_reminding = sum(
                [payment_id.pre_payment_reminding if payment_id.state == 'paid' else 0 for payment_id in
                 employee.payment_ids])
            if not float_is_zero(employee.pre_payment_reminding, precision_rounding=2):
                employee.has_prepayment_ids = True
            else:
                employee.has_prepayment_ids = False

    # 该员工是否有暂支
    has_prepayment_ids = fields.Boolean(compute=_get_pre_payment_reminding)

    pre_payment_reminding = fields.Float(compute=_get_pre_payment_reminding, digits=dp.get_precision('Payroll'))
