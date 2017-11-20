# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrExpense(models.Model):
    _inherit = 'hr.expense'
    _order = 'date asc'

    department_id = fields.Many2one('hr.department', string=u'部门', related='sheet_id.department_id')
    doc = fields.Binary(attachment=True, string=u'附件')
    sale_id = fields.Many2one('sale.order')
    expense_no = fields.Char(related='sheet_id.expense_no')
    product_id = fields.Many2one('product.product', string='Product', readonly=True,
                                 states={'draft': [('readonly', False)], 'refused': [('readonly', False)],
                                         'done': [('readonly', False)]},
                                 domain=[('can_be_expensed', '=', True)], required=True)

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if expense.sheet_id.state == 'done':
                expense.state = "done"
            else:
                expense.state = "draft"

    # 产品变更不影响价格
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account
