# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _, SUPERUSER_ID


_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    """
    采购单
    """
    _inherit = 'purchase.order'

    product_count = fields.Float(compute='get_product_count')
    tax_id = fields.Many2one('account.tax', string='Tax')
    @api.model
    def _default_notes(self):
        return self.env.user.company_id.purchase_note
    notes = fields.Text('Terms and conditions', default=_default_notes)

    @api.onchange('tax_id')
    def onchange_tax_id(self):
        for line in self.order_line:
            line.tax_ids = [(6, 0, [self.tax_id.id])]

    def get_product_count(self):
        count = 0.0
        for line in self.order_line:
            count += line.product_qty
        self.product_count = count




class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_specs = fields.Text(string=u'产品规格', related='product_id.product_specs')

    # 重写默认税的选择
    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        product_lang = self.product_id.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
        })
        self.name = product_lang.display_name
        if product_lang.description_purchase:
            self.name += '\n' + product_lang.description_purchase

        fpos = self.order_id.fiscal_position_id

        self.taxes_id =self.order_id.tax_id



        self._suggest_quantity()
        self._onchange_quantity()

        return result