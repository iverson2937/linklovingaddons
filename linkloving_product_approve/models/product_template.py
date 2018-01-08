# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    state = fields.Selection([
        ('draft', '草稿'),
        ('research ', '研发审核'),
        ('counter_signed', '部门会签'),
        ('done ', '正式')
    ], default='draft')

    def submit(self):
        self.state = 'research'
