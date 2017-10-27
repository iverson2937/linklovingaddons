# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.multi
    @api.returns('procurement.rule', lambda value: value.id if value else False)
    def _find_suitable_rule(self):
        rule = super(ProcurementOrder, self)._find_suitable_rule()
        if self.sale_line_id.order_id.is_scrapy:
            rule = self.env.ref('linkloving_sale_order_import.procurement_rule_retail_shipping')

        return rule
