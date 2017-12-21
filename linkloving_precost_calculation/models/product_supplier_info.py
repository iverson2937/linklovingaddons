# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    def _default_tax_id(self):
        user = self.env.user
        return self.env['account.tax'].search(
            [('company_id', '=', user.company_id.id), ('type_tax_use', '=', 'purchase'),
             ('amount_type', '=', 'percent'), ('account_id', '!=', False)], limit=1, order='amount asc')

    tax_id = fields.Many2one('account.tax', default=_default_tax_id, domain=[('type_tax_use', '=', 'purchase')])


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product. We limit to 10 the number of suppliers for a product to avoid the mess that
        # could be caused for some generic products ("Miscellaneous").
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if partner not in line.product_id.seller_ids.mapped('name') and len(line.product_id.seller_ids) <= 10:
                currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
                supplierinfo = {
                    'name': partner.id,
                    'sequence': max(
                        line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
                    'product_uom': line.product_uom.id,
                    'min_qty': 0.0,
                    'price': self.currency_id.compute(line.price_unit, currency),
                    'currency_id': currency.id,
                    'delay': 0,
                }
                if line.taxes_id:
                    tax_id = line.taxes_id[0].id
                    supplierinfo.update({
                        'tax_id': tax_id
                    })
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError:  # no write access rights -> just ignore
                    break
