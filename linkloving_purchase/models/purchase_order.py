# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo.exceptions import UserError
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
    remark = fields.Text(string='Remark')
    handle_date = fields.Datetime()
    product_id = fields.Many2one(related='order_line.product_id')

    invoice_status = fields.Selection([
        ('no', u'待出货'),
        ('to invoice', u'待对账'),
        ('invoiced', u'已对账完成'),
    ], string=u'对账单状态', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')

    @api.depends('order_line.move_ids')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                # modify by allen 显示隐藏的
                # moves = moves.filtered(lambda r: r.state != 'cancel')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)

    @api.onchange('handle_date')
    def onchange_handle_date(self):
        for line in self.order_line:
            line.date_planned = self.handle_date

    @api.model
    def _default_notes(self):
        return self.env.user.company_id.purchase_note

    notes = fields.Text('Terms and conditions', default=_default_notes)

    @api.onchange('tax_id')
    def onchange_tax_id(self):
        for line in self.order_line:
            line.taxes_id = [(6, 0, [self.tax_id.id])]

    def get_product_count(self):
        count = 0.0
        for line in self.order_line:
            count += line.product_qty
        self.product_count = count


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_specs = fields.Text(string=u'Specification', related='product_id.product_specs')

    def get_draft_po_qty(self, product_id):
        pos = self.env["purchase.order"].search([("state", "in", ("make_by_mrp", "draft"))])
        chose_po_lines = self.env["purchase.order.line"]
        total_draft_order_qty = 0
        for po in pos:
            for po_line in po.order_line:
                if po_line.product_id.id == product_id.id:
                    chose_po_lines += po_line
                    total_draft_order_qty += po_line.product_qty
        return total_draft_order_qty

    @api.depends('product_id.outgoing_qty', 'product_id.incoming_qty', 'product_id.qty_available')
    def _get_output_rate(self):
        on_way_qty = self.get_draft_po_qty(self.product_id) + self.product_id.incoming_qty
        if self.product_id.outgoing_qty:
            rate = ((self.product_id.incoming_qty + self.product_id.qty_available) / self.product_id.outgoing_qty)
            rate = round(rate, 2)

            self.output_rate = (u"( 在途量: " + "%s " + u"+库存:" + "%s ) /"u" 需求量：" + "%s = %s") % (
                on_way_qty, self.product_id.qty_available, self.product_id.outgoing_qty, rate)
        else:
            self.output_rate = (u" 在途量: " + "%s  " + u"库存:" + "%s  "u" 需求量：" + "%s  ") % (
                on_way_qty, self.product_id.qty_available, self.product_id.outgoing_qty)

    output_rate = fields.Char(compute=_get_output_rate, string=u'生产参考')

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

        self.taxes_id = self.order_id.tax_id

        self._suggest_quantity()
        self._onchange_quantity()

        if self.order_id.handle_date:
            self.date_planned = self.order_id.handle_date
        return result

    invoice_status = fields.Selection([
        ('no', u'待出货'),
        ('to invoice', u'待对账'),
        ('invoiced', u'已对账完成'),
    ], string=u'对账单状态', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')
