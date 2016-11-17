# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
import time


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'order_id.tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.category_id.id != self.product_uom.category_id.id):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name
        # modify by allen redefine our price level
        self._compute_tax_id()
        # if self.order_id.pricelist_id and self.order_id.partner_id:
        #     vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product),
        #                                                                          product.taxes_id, self.tax_id)
        discount_obj = self.env['product.price.discount']
        partner_id = self.order_id.partner_id
        product_id = self.product_id
        tax_id = self.tax_id

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
            if not tax_id.amount:
                vals['price_unit'] = self.product_id.price1 * discount
            else:
                vals['price_unit'] = self.product_id.price1_tax * discount_tax
        elif partner_id.level == 2:
            if not tax_id.amount:
                vals['price_unit'] = product_id.price2 * discount
            else:
                vals['price_unit'] = product_id.price2_tax * discount_tax
        else:
            if not tax_id.amount:
                vals['price_unit'] = product_id.price3 * discount
            else:
                vals['price_unit'] = product_id.price3_tax * discount_tax
        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {'domain': domain}

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )


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
                if partner_id.level == 1:
                    if not line.tax_id.amount:
                        price = line.product_id.price1
                    else:
                        price = line.product_id.price1_tax
                elif partner_id.level == 2:
                    if not line.tax_id.amount:
                        price = line.product_id.price2
                    else:
                        price = line.product_id.price2_tax
                elif partner_id.level == 3:
                    if not line.tax_id.amount:
                        price = line.product_id.price3
                    else:
                        price = line.product_id.price3_tax
                if price and not line.tax_id.amount and price_unit <> price:
                    discount = price_unit / price
                    discount_obj.price = discount
                elif price and line.tax_id.amount and price_unit <> price:
                    discount_tax = price_unit / price
                    discount_obj.price_tax = discount_tax

        return super(SaleOrderLine, self).write(vals)

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            line.tax_id = line.order_id.tax_id

    @api.model
    def create(self, vals):
        order_id = self.env['sale.order'].browse(vals.get('order_id'))
        if vals.get('tax_id'):
            #FIXme:
            try:
                _, _, tax_id = vals.get('tax_id')[0]
                if tax_id:
                    tax_id=tax_id[0]
            except Exception:
                _,tax_id=vals.get('tax_id')[1]
            tax_id = self.env['account.tax'].browse(tax_id)

        price_unit = vals.get('price_unit')
        product_id = self.env['product.product'].browse(vals.get('product_id'))
        price = 0.0
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
                if not tax_id.amount:
                    price = product_id.price1
                else:
                    price = product_id.price1_tax
            elif partner_id.level == 2:
                if not tax_id.amount:
                    price = product_id.price2
                else:
                    price = product_id.price2_tax
            elif partner_id.level == 3:
                if not tax_id.amount:
                    price = product_id.price3
                else:
                    price = product_id.price3_tax
            if price and not tax_id.amount and price_unit <> price:
                discount = price_unit / price
                discount_obj.price = discount
            elif price and tax_id.amount and price_unit <> price:
                discount_tax = price_unit / price
                discount_obj.price_tax = discount_tax

        return super(SaleOrderLine, self).create(vals)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            print amount_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })
            print order.amount_untaxed


    @api.onchange('tax_id')
    def _onchange_tax_id(self):
        discount = discount_tax = 1.0
        if self.order_line:

            for line in self.order_line:
                discount_id = self.env['product.price.discount'].search(
                    [('partner_id', '=', self.partner_id.id), ('product_id', '=', line.product_id.id)], limit=1)
                line.tax_id= [(6, 0, [self.tax_id.id])]
                if discount_id:
                    discount = discount_id.price
                    discount_tax = discount_id.price_tax
                if self.partner_id.level == 1:
                    if self.tax_id.amount:
                        line.price_unit = line.product_id.price1_tax * discount_tax
                    else:
                        line.price_unit = line.product_id.price1 * discount
                elif self.partner_id.level == 2:
                    if self.tax_id.amount:
                        line.price_unit = line.product_id.price2_tax * discount_tax
                    else:
                        line.price_unit = line.product_id.price2 * discount
                elif self.partner_id.level == 3:
                    if self.tax_id.amount:
                        line.price_unit = line.product_id.price2_tax * discount_tax
                    else:
                        line.price_unit = line.product_id.price2 * discount
