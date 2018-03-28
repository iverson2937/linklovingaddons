# -*- coding: utf-8 -*-

from odoo import models, fields


class linkloving_work_order_tag(models.Model):
    _name = 'linkloving.work.order.tag'

    name = fields.Char()

    brand_ids = fields.Many2one('product.category.brand')

    area_ids = fields.Many2one('product.category.area')

    product_ids = fields.Many2one('product.category')
