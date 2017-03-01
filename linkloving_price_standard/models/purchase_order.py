# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
import time

from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        product_lang = self.product_id.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
        })
        self.name = product_lang.display_name
        if product_lang.description_purchase:
            self.name += '\n' + product_lang.description_purchase

        fpos = self.order_id.fiscal_position_id
        if self.env.uid == SUPERUSER_ID:
            company_id = self.env.user.company_id.id
            self.taxes_id = fpos.map_tax(
                self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
        else:
            self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)

        self._suggest_quantity()
        self._onchange_quantity()

        return result

    def _onchange_quantity(self):
        if not self.product_id:
            return

        self._compute_taxes_id()
        discount_obj = self.env['product.price.discount']
        partner_id = self.order_id.partner_id
        product_id = self.product_id
        taxes_id = self.taxes_id
        discount_id = discount_obj.search(
            [('partner_id', '=', partner_id.id), ('product_id', '=', product_id.id)])
        if not discount_id:
            discount_id = discount_obj.create({
                'partner_id': partner_id.id,
                'product_id': product_id.id
            })
        price = 0.0
        discount = discount_id.price
        discount_tax = discount_id.price_tax
        if partner_id.level == 1:
            if not taxes_id.amount:
                self.price_unit = self.product_id.price1 * discount
            else:
                self.price_unit = self.product_id.price1_tax * discount_tax
        elif partner_id.level == 2:
            if not taxes_id.amount:
                self.price_unit = product_id.price2 * discount
            else:
                self.price_unit = product_id.price2_tax * discount_tax
        else:
            if not taxes_id.amount:
                self.price_unit = product_id.price3 * discount
            else:
                self.price_unit = product_id.price3_tax * discount_tax

    @api.multi
    def write(self, vals):
        for line in self:
            price_unit = vals.get('price_unit')
            price = 0.0

            if price_unit:
                product_id = vals.get('product_id') or line.product_id.id
                partner_id = line.order_id.partner_id
                discount_obj = line.env['product.price.discount'].search(
                    [('partner_id', '=', partner_id.id), ('product_id', '=', product_id)])
                if not discount_obj:
                    discount_obj = self.env['product.price.discount'].create({
                        'partner_id': partner_id.id,
                        'product_id': product_id
                    })
                if partner_id.level == 1:
                    if not line.taxes_id.amount:
                        if not line.product_id.price1:
                            line.product_id.price1 = price_unit
                        else:
                            price = line.product_id.price1
                    else:
                        if not line.product_id.price1_tax:
                            line.product_id.price1_tax = price_unit
                        else:
                            price = line.product_id.price1_tax
                elif partner_id.level == 2:
                    if not line.taxes_id.amount:
                        if not line.product_id.price2:
                            line.product_id.price2 = price_unit
                        else:
                            price = line.product_id.price2
                    else:
                        if not line.product_id.price2_tax:
                            line.product_id.price2_tax = price_unit
                        else:
                            price = line.product_id.price2_tax
                elif partner_id.level == 3:
                    if not line.taxes_id.amount:
                        if not line.product_id.price3:
                            line.product_id.price3 = price_unit
                        else:
                            price = line.product_id.price3
                    else:
                        if not line.product_id.price3_tax:
                            line.product_id.price3_tax = price_unit
                        else:
                            price = line.product_id.price3_tax
                if price and not line.taxes_id.amount and price_unit <> price:
                    discount = price_unit / price
                    discount_obj.price = discount
                elif price and line.taxes_id.amount and price_unit <> price:
                    discount_tax = price_unit / price
                    discount_obj.price_tax = discount_tax

        return super(PurchaseOrderLine, self).write(vals)

    @api.multi
    def _compute_taxes_id(self):
        for line in self:
            line.taxes_id = line.order_id.tax_id

    @api.model
    def create(self, vals):
        order_id = self.env['purchase.order'].browse(vals.get('order_id'))

        taxes_id = self.resolve_2many_commands('taxes_id', vals.get('taxes_id'))
        if not taxes_id:
            raise UserError('请设置税率')
        amount = taxes_id[0].get('amount')

        price_unit = vals.get('price_unit')
        price = 0.0
        product_id = self.env['product.product'].browse(vals.get('product_id'))
        if price_unit:
            partner_id = order_id.partner_id
            discount_obj = self.env['product.price.discount'].search(
                [('partner_id', '=', partner_id.id), ('product_id', '=', product_id.id)])
            if not discount_obj:
                discount_obj = self.env['product.price.discount'].create({
                    'partner_id': partner_id.id,
                    'product_id': product_id.id
                })

            if partner_id.level == 1:
                if not amount:
                    if not product_id.price1:
                        product_id.price1 = price_unit
                    else:
                        price = product_id.price1
                else:
                    if not product_id.price1_tax:
                        product_id.price1_tax = price_unit
            elif partner_id.level == 2:
                if not amount:
                    if not product_id.price2:
                        product_id.price2 = price_unit
                else:
                    if not product_id.price2_tax:
                        product_id.price2_tax = price_unit
            elif partner_id.level == 3:
                if not amount:
                    if not product_id.price3:
                        product_id.price3 = price_unit
                else:
                    if not product_id.price3_tax:
                        product_id.price3_tax = price_unit
            if price and not amount and price_unit <> price:
                discount = price_unit / price
                discount_obj.price = discount
            elif price and amount and price_unit <> price:
                discount_tax = price_unit / price
                discount_obj.price_tax = discount_tax

        return super(PurchaseOrderLine, self).create(vals)
