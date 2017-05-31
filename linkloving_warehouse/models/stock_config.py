# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from odoo import api, fields, models


class StockConfigSettings(models.TransientModel):
    _inherit = 'stock.config.settings'

    # -*- coding: utf-8 -*-
    # Part of Odoo. See LICENSE file for full copyright and licensing details.

    from odoo import api, fields, models

    class StockConfigSettings(models.TransientModel):
        _inherit = 'stock.config.settings'

        @api.multi
        def rename(self):
            products = self.env['product.template'].search([])
            for product in products:
                if re.findall(r"{-RT-CN}", product.name):
                    continue
                old = re.findall(r"-RT-CN", product.name)
                new_name = ''
                if old:
                    new_name = product.name.replace(old[0], "{RT-CN}")
                if new_name:
                    product.name = new_name
