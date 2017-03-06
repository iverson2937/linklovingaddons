# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductProduct(models.Model):
    """
       添加多级报价
    """
    _inherit = 'product.template'
    price1 = fields.Float(string=u'1st no tax price')
    price2 = fields.Float(string=u'2nd no tax price')
    price3 = fields.Float(string=u'3rd no tax price')
    price1_tax = fields.Float(string=u'1st tax included price')
    price2_tax = fields.Float(string=u'2nd tax included price')
    price3_tax = fields.Float(string=u'3rd tax included price')


class ProductPriceDiscount(models.Model):
    """
       添加多级报价
    """
    _name = 'product.price.discount'
    partner_id = fields.Many2one('res.partner')
    product_id = fields.Many2one('product.product')
    price = fields.Float(default=1.00)
    price_tax = fields.Float(default=1.00)
