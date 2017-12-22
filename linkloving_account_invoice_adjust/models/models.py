# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoiceAdjust(models.Model):
    _name = 'account.invoice.adjust'
    _inherits = {'product.product': 'product_id'}
    type_mode = fields.Selection([
        ('minus', '减少'),
        ('add', '添加')
    ])
    product_id = fields.Many2one('product.product', string='Delivery Product', required=True, ondelete="cascade")
