# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class AccountEmployeeRegisterPaymentWizard(models.TransientModel):
    _name = "account.employee.payable.wizard"
    _description = "Hr Expense Register Payment wizard"

    @api.model
    def _get_default_sheet_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        sheet_id = self.env['hr.expense.sheet'].browse(active_ids)
        return sheet_id

    sheet_id = fields.Many2one('hr.expense.sheet', default=_get_default_sheet_id)
    employee_id = fields.Many2one('hr.employee', readonly=1)

    @api.model
    def _get_default_payment_id(self):
        payment_ids = self.env['account.employee.payment'].search(
            [('state', '=', 'paid'), ('employee_id', '=', self._context.get('employee_id'))])
        if payment_ids:
            return payment_ids[0]

    payment_ids = fields.Many2many('account.employee.payment', readonly=1)

    @api.depends('payment_ids')
    def _compute_deduct_amount(self):
        amount = 0.0
        for payment_id in self.payment_ids:
            amount += payment_id.pre_payment_reminding
        self.deduct_amount = amount

    deduct_amount = fields.Float(compute=_compute_deduct_amount)

    @api.multi
    def process(self):
        if not self.payment_ids:
            raise UserError('你还未选择暂支单')
        total_amount = self.sheet_id.total_amount - self.sheet_id.payment_line_amount
        if not self.sheet_id:
            raise UserError(u'未找到报销单')
        for payment_id in sorted(self.payment_ids, key=lambda x: x.pre_payment_reminding):
            if total_amount:
                line_id = self.env['account.employee.payment.line'].create({
                    'payment_id': payment_id.id,
                    'sheet_id': self.sheet_id.id,
                    'amount': payment_id.pre_payment_reminding if payment_id.pre_payment_reminding <= total_amount else total_amount
                })
                total_amount -= line_id.amount
                # 报销单金额大于所以暂支单金额
                # self.sheet_id.process()
                # # 报销单状态
                # if float_is_zero(total_amount, 2):
                #     self.sheet_id.state = 'done'
                # else:
                #     # 不知道是否有这样的情况。。。
                #     self.sheet_id.state = 'post'

    @api.multi
    def no_deduct_process(self):
        self.sheet_id.process()
