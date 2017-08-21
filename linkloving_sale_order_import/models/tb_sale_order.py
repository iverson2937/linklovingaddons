# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api


class TBSaleOrder(models.Model):
    _inherit = 'eb.order'

    total_amount = fields.Float(string=u'订单金额')
    deal_date = fields.Datetime(string=u'成交日期')
    shipping_date = fields.Datetime(string=u'发货日期')

    @api.model
    def create(self, vals):
        eb_order = super(TBSaleOrder, self).create(vals)
        print eb_order, 'dddddddddddddd'
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

    def create_eb_sale_order(self, vals):
        order_id = self.search([('name', '=', vals.get('name'))], limit=1)
        partner_id = self.env.ref("linkloving_eb.res_partner_eb_customer")
        delivery_fee = vals.get('delivery_fee')

        print partner_id, 'ddddddddddddddddsfsdfsf'

        if not order_id:
            product_id = self.env['product.product'].search([('default_code', '=', '98.0A4000.104')])
            line_ids = []
            # for line in vals.get('items'):
            # product_id = self.env['product.product'].search([('default_code', '=', '98.0A4000.104')])
            # line_id = self.env['eb.order.line'].create({
            #     'product': line.get('product'),
            #     'product_id': product_id.id,
            #     'price_unit': line.price_unit,
            #     'product_qty': line.product_qty,
            # })
            # line_ids.append(line_id)
            eb_order_id = self.create({
                'name': vals.get('name'),
                'partner_id': partner_id.id,
                'total_amount': vals.get('total_amount'),
                'deal_date': datetime.datetime.strptime(str(vals.get('deal_date').strip()), '%Y-%m-%d %H:%M'),
                'eb_order_line_ids': [(0, 0, {
                    'product_id': product_id.id,
                    'product': item.get('product'),
                    'price_unit': item.get('price_unit'),
                    'qty': item.get('product_qty')

                }) for item in vals.get('items')],
            })
            # 添加运费
            if delivery_fee:
                delivery_fee_id = self.env['product.product'].search([('default_code', '=', '003')])
                self.env['eb.order.line'].create({
                    'product_id': delivery_fee_id.id,
                    'product': u'运费',
                    'price_unit': delivery_fee,
                    'qty': 1,
                    'eb_order_id': eb_order_id,
                })

        else:
            if not order_id.shipping_date:
                order_id.shipping_date = vals.get('shipping_date')

    class TBSaleOrderLine(models.Model):
        _inherit = 'eb.order.line'
        product = fields.Char(string=u'产品')
        price_unit = fields.Float(string=u'采购价')
