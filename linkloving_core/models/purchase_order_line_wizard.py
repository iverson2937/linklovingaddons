# -*- coding: utf-8 -*-
import json
from datetime import datetime

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
    product_uom = fields.Many2one('product.uom')
    date_planned = fields.Datetime(string=u'计划交期')

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        self.product_uom = self.product_id.uom_id

    @api.model
    def create(self, vals):
        wizard = super(PurchaseOrderLineWizard, self).create(vals)
        self.env['purchase.order'].create({
            'name': 'New',
            'partner_id': wizard.partner_id.id,
            'handle_date': wizard.date_planned,
            'order_line': [(0, 0, {
                'product_id': wizard.product_id.id,
                'product_qty': wizard.product_uom_qty,
                'price_unit': wizard.price_unit,
                'product_uom': wizard.product_uom.id,
                'name': wizard.product_id.display_name,
                'date_planned': wizard.date_planned
            })]

        })
        return super(PurchaseOrderLineWizard, self).create(vals)
