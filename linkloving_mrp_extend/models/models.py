# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    product_specs = fields.Text(string=u'产品规格', related='product_tmpl_id.product_specs')

# class linkloving_mrp_extend(models.Model):
#     _name = 'linkloving_mrp_extend.linkloving_mrp_extend'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100