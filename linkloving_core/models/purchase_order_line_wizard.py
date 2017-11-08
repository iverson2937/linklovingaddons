# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api
from models import MO_STATE
import uuid

from odoo.exceptions import UserError


class PurchaseOrderLineWizard(models.TransientModel):
    _name = 'purchase.order.line.wizard'
    partner_id = fields.Many2one('res.partner', string=u'供应商',
                                 domain=[('is_company', '=', True), ('supplier', '=', True)])
    product_id = fields.Many2one('product.product', string=u'产品')
    product_uom_qty = fields.Float(string=u'数量', default=1.0)
    price_unit = fields.Float(string=u'单价')

    @api.model
    def create(self, vals):
        self.env['purchase.order'].create({
            'partner_id': vals.get('partner_id'),
            'order_line': [(0, 0, {
                'product_id': vals.get('product_id'),
                'product_uom_qty': float(vals.get('product_uom_qty')),
                'price_unit': float(vals.get('orderPrice')),
            })]

        })
        return super(PurchaseOrderLineWizard, self).create(vals)
