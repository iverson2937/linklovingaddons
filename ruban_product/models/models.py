# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    l_size = fields.Float(string=u'长')
    wide = fields.Float(string=u'宽')
    high = fields.Float(string=u'高')
