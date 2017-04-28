# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _name = 'product.template'
    is_domestic = fields.Boolean()
