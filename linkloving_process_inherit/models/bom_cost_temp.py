# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BomCostCategoryTemp(models.Model):
    _name = 'bom.cost.category.temp'
    category_id = fields.Many2one('product.category')
    product_id = fields.Many2one('product.product')
    action_data = fields.Char()

    # @api.model
    # def create_temp_data(self, category_id, p_product_id, product_id, action_id_1, rate1, action_id_2, rate2):
    #     vals = {
    #         'category_id': category_id,
    #         'p_product_id': p_product_id,
    #         'product_id': product_id,
    #         'action_id_1': action_id_1,
    #         'rate1': rate1,
    #         'action_id_2': action_id_2,
    #         'rate2': rate2
    #     }
    #     self.env['bom.cost.category.temp'].create(vals)
