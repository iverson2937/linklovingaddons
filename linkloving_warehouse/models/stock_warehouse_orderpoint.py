# -*- coding: utf-8 -*-


from odoo import fields, models, _, api
from odoo.exceptions import UserError


class stockWarehouseOrderpoint(models.Model):
    """
    订货规则
    """

    _inherit = 'stock.warehouse.orderpoint'

    @api.multi
    def write(self, vals):
        if self.product_id.status == 'eol' and vals.get('active'):
            raise UserError('停产的产品不能激活订货规则')
        return super(stockWarehouseOrderpoint, self).write(vals)
