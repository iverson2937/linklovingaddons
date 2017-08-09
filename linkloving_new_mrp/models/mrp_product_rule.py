# -*- coding: utf-8 -*-
import math

import datetime
from odoo import models, fields, api, _


class MrpProductRule(models.Model):
    _name = 'mrp.product.rule'
    name = fields.Char(string='名称')

    output_product_ids = fields.One2many('mrp.product.rule.line', 'rule_id', domain=[('type', '=', 'output')],
                                         required=1)
    input_product_ids = fields.One2many('mrp.product.rule.line', 'rule_id', domain=[('type', '=', 'input')], required=1)

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            product_id = self.resolve_2many_commands('input_product_ids', vals.get('input_product_ids'))[0]
            vals['name'] = self.env['product.product'].browse(product_id.get('product_id')).name
        return super(MrpProductRule, self).create(vals)


class MrpProductRuleLine(models.Model):
    _name = 'mrp.product.rule.line'
    rule_id = fields.Many2one('mrp.product.rule', on_delete="cascade")
    mo_id = fields.Many2one('mrp.product.rule', on_delete="cascade")
    product_id = fields.Many2one('product.product')
    produce_qty = fields.Float(default=1.0)
    type = fields.Selection([
        ('input', u'投入'),
        ('output', u'产出'),
    ])

    @api.multi
    def write(self, vals):
        if 'rule_id' in vals:
            vals.pop('rule_id')
        return super(MrpProductRuleLine, self).write(vals)

    @api.multi
    def unlink(self):
        return super(MrpProductRuleLine, self).unlink()
