# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    def _default_tax_id(self):
        user = self.env.user
        return self.env['account.tax'].search(
            [('company_id', '=', user.company_id.id), ('type_tax_use', '=', 'purchase'),
             ('amount_type', '=', 'percent'), ('account_id', '!=', False)], limit=1, order='amount asc')

    tax_id = fields.Many2one('account.tax', default=_default_tax_id, domain=[('type_tax_use', '=', 'purchase')])
