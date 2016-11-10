# -*- coding: utf-8 -*-
import logging
import threading

from openerp import models, fields, api, _, SUPERUSER_ID
from openerp import tools
from openerp.osv import osv

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    """
    采购单
    """
    _inherit = 'purchase.order'

    product_count = fields.Float(compute='get_product_count')

    def get_product_count(self):
        count = 0.0
        for line in self.order_line:
            count += line.product_qty
        self.product_count = count


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    po_id = fields.Many2one('purchase.order')
