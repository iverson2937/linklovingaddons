# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api


class RetailSaleOrder(models.Model):
    _name = 'retail.order'
    name = fields.Char(string=u'名称')
    partner_id = fields.Many2one('res.partner')
    total_amount = fields.Float(string=u'订单金额', track_visibility='onchange')
    order_date = fields.Datetime(string=u'成交日期/下单时间', track_visibility='onchange')
    payment_date = fields.Datetime(string=u'付款日期')
    finish_date = fields.Datetime(string=u'完成日期')
    shipping_date = fields.Datetime(string=u'发货日期', track_visibility='onchange')
    sales_promotion = fields.Float(string=u'促销金额')
    coupon_price = fields.Float(string=u'优惠券')
    actual_payment = fields.Float(string=u'实付金额')
    is_refund = fields.Boolean(string=u'退款申请')
    state = fields.Selection([
        ('draft', u'草稿'),
        ('error', u'异常'),
        ('done', u'完成')
    ])
    order_status = fields.Char(string=u'订单状态')
    order_line_ids = fields.One2many('retail.order.line', 'order_id')

    @api.model
    def create(self, vals):
        print vals, 'ddddddd'
        eb_order = super(RetailSaleOrder, self).create(vals)
        # tax_id = self.env["account.tax"].search([('type_tax_use', '<>', "purchase")], limit=1)[0].id
        # order_id = self.env["sale.order"].create({
        #     'partner_id': eb_order.partner_id.id,
        #     'partner_invoice_id': eb_order.partner_id.id,
        #     'partner_shipping_id': eb_order.partner_id.id,
        #     'tax_id': tax_id,
        #     'order_line': [(0, 0, {'name': p.product_id.name,
        #                            'product_id': p.product_id.id,
        #                            'product_uom_qty': p.qty,
        #                            'product_uom': p.product_id.uom_id.id,
        #                            'price_unit': p.price_unit,
        #                            'tax_id': [(6, 0, [tax_id])]}) for p in eb_order.order_line_ids],
        # })
        # eb_order.order_id = order_id.id
        return eb_order

    def create_retail_sale_order(self, values, partner_id=False):
        name, vals = values.items()[0]
        items = vals.get('items')
        order_id = self.search([('name', '=', name)], limit=1)
        delivery_fee = vals.get('delivery_fee', 0.00)

        delivery_fee_id = self.env.ref('linkloving_sale_order_import.product_product_delivery_cost')

        if not order_id:

            order_id = self.create({
                'name': name,
                'total_amount': vals.get('total_amount'),
                'partner_id': partner_id,
                'order_date': vals.get('order_date'),
                'finish_date': vals.get('finish_date'),
                'payment_date': vals.get('payment_date'),
                'shipping_date': vals.get('shipping_date'),
                'order_status': vals.get('order_status'),
                'sales_promotion': vals.get('sales_promotion'),
                'coupon_price': vals.get('coupon_price'),
                'actual_payment': vals.get('actual_payment')
            })
            # 添加运费
            if delivery_fee:
                self.env['retail.order.line'].create({
                    'product_id': delivery_fee_id.id,
                    'product': u'运费',
                    'price_unit': delivery_fee,
                    'product_qty': 1,
                    'order_id': order_id.id,
                })
            if vals.get('discount'):
                self.env['retail.order.line'].create({
                    'product_id': self.env.ref('linkloving_sale_order_import.product_product_discount'),
                    'product': u'折扣',
                    'price_unit': -vals.get('discount'),
                    'product_qty': 1,
                    'order_id': order_id.id,
                })
            if vals.get('sales_promotion'):
                self.env['retail.order.line'].create({
                    'product_id': self.env.ref('linkloving_sale_order_import.product_product_sales_promotion'),
                    'product': u'促销',
                    'price_unit': -vals.get('sales_promotion'),
                    'product_qty': 1,
                    'order_id': order_id.id,
                })
            if vals.get('coupon_price'):
                self.env['retail.order.line'].create({
                    'product_id': self.env.ref('linkloving_sale_order_import.product_product_coupon_price'),
                    'product': u'优惠卷',
                    'price_unit': -vals.get('coupon_price'),
                    'product_qty': 1,
                    'order_id': order_id.id,
                })

            if items:
                for item in items:
                    product_id = False
                    if item.get('default_code'):
                        product_id = self.env['product.product'].search(['default_code', '=', item.get('default_code')])
                    if not product_id:
                        order_id.state = 'error'
                    self.env['retail.order.line'].create({
                        'product_id': product_id.id if product_id else False,
                        'description': item.get('description'),
                        'product': item.get('product'),
                        'price_unit': item.get('price_unit'),
                        'product_qty': item.get('product_qty'),
                        'order_id': order_id.id,
                    })
        else:
            order_id.write({
                'total_amount': vals.get('total_amount'),
                'order_date': vals.get('order_date'),
                'finish_date': vals.get('finish_date'),
                'payment_date': vals.get('payment_date'),
                'shipping_date': vals.get('shipping_date'),
                'order_status': vals.get('order_status'),
                'sales_promotion': vals.get('sales_promotion'),
                'coupon_price': vals.get('coupon_price'),
                'actual_payment': vals.get('actual_payment'),
            })
            for item in vals.get('items'):
                if item.get('default_code'):
                    product_id = self.env['product.product'].search(['default_code', '=', item.get('default_code')])
                    line_id = self.order_line_ids.filtered(lambda x: x.product_id == product_id)
                    if line_id:
                        line_id.write({
                            'price_unit': item.get('price_unit'),
                            'product_qty': item.get('product_qty'),
                            'description': item.get('description'),
                        })
                    else:
                        self.env['retail.order.line'].create({
                            'product_id': product_id.id if product_id else False,
                            'description': item.get('description'),
                            'product': item.get('product'),
                            'price_unit': item.get('price_unit'),
                            'product_qty': item.get('product_qty'),
                            'order_id': order_id.id,
                        })
                        # if delivery_fee:
                        #     fee_id = self.order_line_ids.filtered(lambda x: x.product_id == delivery_fee_id.id)
                        #     if fee_id:
                        #         fee_id.write({
                        #             'price_unit': delivery_fee,
                        #         })
                        #     else:
                        #         self.env['retail.order.line'].create({
                        #             'product_id': delivery_fee_id.id,
                        #             'description': u'运费',
                        #             'price_unit': delivery_fee,
                        #             'qty': 1,
                        #             'order_id': order_id.id,
                        #         })


class RetailSaleOrderLine(models.Model):
    _name = 'retail.order.line'
    order_id = fields.Many2one('retail.order')
    product_id = fields.Many2one('product.product')
    discount = fields.Float(string=u'折扣')
    product_qty = fields.Float(string=u'数量')
    price_unit = fields.Float(string=u'单价')
    description = fields.Char(string=u'描述')
    product_name = fields.Char(string=u'描述')
    purchase_price = fields.Float(string=u'采购价')
