# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api


class RetailSaleOrder(models.Model):
    _name = 'retail.order'
    name = fields.Char(string=u'名称')
    partner_id = fields.Many2one('res.partner')
    total_amount = fields.Float(string=u'订单金额', track_visibility='onchange')
    deal_date = fields.Datetime(string=u'成交日期', track_visibility='onchange')
    shipping_date = fields.Datetime(string=u'发货日期', track_visibility='onchange')
    state = fields.Selection([
        ('draft', u'草稿'),
        ('error', u'异常'),
        ('done', u'完成')
    ])
    order_line_ids = fields.One2many('retail.order.line', 'order_id')

    @api.model
    def create(self, vals):
        eb_order = super(RetailSaleOrder, self).create(vals)
        tax_id = self.env["account.tax"].search([('type_tax_use', '<>', "purchase")], limit=1)[0].id
        order_id = self.env["sale.order"].create({
            'partner_id': eb_order.partner_id.id,
            'partner_invoice_id': eb_order.partner_id.id,
            'partner_shipping_id': eb_order.partner_id.id,
            'tax_id': tax_id,
            'order_line': [(0, 0, {'name': p.product_id.name,
                                   'product_id': p.product_id.id,
                                   'product_uom_qty': p.qty,
                                   'product_uom': p.product_id.uom_id.id,
                                   'price_unit': p.price_unit,
                                   'tax_id': [(6, 0, [tax_id])]}) for p in eb_order.eb_order_line_ids],
        })
        eb_order.order_id = order_id.id
        return eb_order

    def create_detail_sale_order(self, vals):
        order_id = self.search([('name', '=', vals.get('name'))], limit=1)
        partner_id = self.env.ref("linkloving_eb.res_partner_eb_customer")
        delivery_fee = vals.get('delivery_fee')
        shipping_date = vals.get('shipping_date')
        total_amount = vals.get('total_amount')
        name = vals.get('name')

        items = vals.get('items')
        delivery_fee_id = self.env.ref('linkloving_sale_order_import.product_product_delivery_cost')

        if not order_id:

            order_id = self.create({
                'name': name,
                'partner_id': partner_id.id,
                'total_amount': total_amount,
                'deal_date': datetime.datetime.strptime(str(vals.get('deal_date').strip()), '%Y-%m-%d %H:%M'),
                'shipping_date': shipping_date,
                'order_line_ids': [(0, 0, {
                    'product': item.get('product'),
                    'price_unit': item.get('price_unit'),
                    'qty': item.get('product_qty'),
                    'description': item.get('description')
                }) for item in vals.get('items')],
            })
            # 添加运费
            if delivery_fee:
                self.env['retail.order.line'].create({
                    'product_id': delivery_fee_id.id,
                    'description': u'运费',
                    'price_unit': delivery_fee,
                    'qty': 1,
                    'eb_order_id': order_id,
                })
            if items:
                for item in items:
                    product_id = self.env['product.product'].search(['default_code', '=', item.get('default_code')])
                    if not product_id:
                        order_id.state = 'error'
                    self.env['retail.order.line'].create({
                        'product_id': product_id.id if product_id else False,
                        'description': item.get('description'),
                        'product': item.get('product'),
                        'price_unit': item.get('price_unit'),
                        'qty': item.get('qty'),
                        'eb_order_id': order_id,
                    })
        else:
            order_id.write({
                'total_amount': vals.get('total_amount'),
                'deal_date': datetime.datetime.strptime(str(vals.get('deal_date').strip()), '%Y-%m-%d %H:%M'),
                'shipping_date': shipping_date,
            })
            for item in vals.get('items'):
                if item.get('default_code'):
                    product_id = self.env['product.product'].search(['default_code', '=', item.get('default_code')])
                    line_id = self.order_line_ids.filtered(lambda x: x.product_id == product_id)
                    if line_id:
                        line_id.write({
                            'price_unit': item.get('price_unit'),
                            'qty': item.get('qty'),
                            'description': item.get('description'),
                        })
                    else:
                        self.env['retail.order.line'].create({
                            'product_id': product_id.id if product_id else False,
                            'description': item.get('description'),
                            'product': item.get('product'),
                            'price_unit': item.get('price_unit'),
                            'qty': item.get('qty'),
                            'eb_order_id': order_id,
                        })
            if delivery_fee:
                fee_id = self.order_line_ids.filtered(lambda x: x.product_id == delivery_fee_id.id)
                if fee_id:
                    fee_id.write({
                        'price_unit': delivery_fee,
                    })
                else:
                    self.env['retail.order.line'].create({
                        'product_id': delivery_fee_id.id,
                        'description': u'运费',
                        'price_unit': delivery_fee,
                        'qty': 1,
                        'eb_order_id': order_id,
                    })


class RetailSaleOrderLine(models.Model):
    _name = 'retail.order.line'
    order_id = fields.Many2one('retail.order')
    product_id = fields.Many2one('product.product')
    qty = fields.Float(string=u'数量')
    price_unit = fields.Float(string=u'单价')
    description = fields.Char(string=u'描述')
