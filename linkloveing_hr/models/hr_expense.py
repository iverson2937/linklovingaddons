# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    department_id = fields.Many2one('hr.department', string=u'部门')
    doc = fields.Binary(attachment=True, string=u'附件')

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if expense.sheet_id:
                expense.state = "draft"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif not expense.sheet_id.account_move_id:
                expense.state = "draft"
            else:
                expense.state = "done"


    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_amount = self.product_id.price_compute('standard_price')[self.product_id.id]
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account
