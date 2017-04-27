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
    product_qty = fields.Float(related='order_line.product_qty')

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
        for order in self:
            for line in order.order_line:
                line.date_planned = order.handle_date

    @api.model
    def _default_notes(self):
        return self.env.user.company_id.purchase_note

    notes = fields.Text('Terms and conditions', default=_default_notes)

    @api.onchange('tax_id')
    def onchange_tax_id(self):
        for line in self.order_line:
            line.taxes_id = [(6, 0, [self.tax_id.id])]

    def get_product_count(self):
        for order in self:
            count = 0.0
            for line in order.order_line:
                count += line.product_qty
            order.product_count = count


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_specs = fields.Text(string=u'Specification', related='product_id.product_specs')

    def get_draft_po_qty(self, product_id):
        pos = self.env["purchase.order"].search([("state", "in", ("make_by_mrp", "draft", "to approve"))])
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
        for line in self:
            draft_qty = line.get_draft_po_qty(line.product_id)
            on_way_qty = draft_qty + line.product_id.incoming_qty
            if line.product_id.outgoing_qty:
                rate = ((
                        draft_qty + line.product_id.incoming_qty + line.product_id.qty_available) / line.product_id.outgoing_qty)
                rate = round(rate, 2)

                line.output_rate = (u"(草稿量: %s+在途量: " + "%s " + u"+库存:" + "%s ) /"u" 需求量：" + "%s = %s") % (
                    draft_qty, line.product_id.incoming_qty, line.product_id.qty_available,
                    line.product_id.outgoing_qty, rate)
            else:
                line.output_rate = (u" 在途量: " + "%s  " + u"库存:" + "%s  "u" 需求量：" + "%s  ") % (
                    on_way_qty, line.product_id.qty_available, line.product_id.outgoing_qty)

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


class manual_combine_po(models.TransientModel):
    _name = "manual.combine.po"

    @api.one
    def action_confirm(self):
        ids = self._context.get("active_ids")
        pos = self.env[self._context.get("active_model")].search([("id", "in", ids)])
        if len(pos.mapped("partner_id").ids) != 1:  # 如果相等 代表不重复
            raise UserError("请选择相同供应商的采购单进行合并.")
        else:
            po_first = pos[0]
            for po in pos[1:]:
                for line in po.order_line:
                    line.order_id = po_first.id
                self.combine_origin(po_first, po)
                po.button_cancel()
                po.unlink()

        same_origin = {}
        for po_line in po_first.order_line:
            if po_line.product_id.id in same_origin.keys():
                same_origin[po_line.product_id.id].append(po_line)
            else:
                same_origin[po_line.product_id.id] = [po_line]

        for key in same_origin.keys():
            po_group = same_origin[key]
            total_qty = 0
            procurements = self.env["procurement.order"]
            for po_line in po_group:
                total_qty += po_line.product_qty
                procurements += po_line.procurement_ids

            # 生成薪的po单 在po0的基础上
            po_group[0].product_qty = total_qty
            po_group[0].procurement_ids = procurements

            for po_line in po_group[1:]:
                po_line.unlink()


    def combine_origin(self, po, po_to_combine):
        if not po.origin:
            return
        if po_to_combine.origin not in po.origin.split(', '):
            # Keep track of all procurements
            if po.origin:
                if po_to_combine.origin:
                    po.write({'origin': po.origin + ', ' + po_to_combine.origin})
                else:
                    po.write({'origin': po.origin})
            else:
                po.write({'origin': po_to_combine.origin})

                #
                # def  combine_aaa:
                #     for line in po.order_line:
                #             if line.product_id == procurement.product_id and line.product_uom == procurement.product_id.uom_po_id:
                #                 procurement_uom_po_qty = procurement.product_uom._compute_quantity(product_new_qty,
                #                                                                                    procurement.product_id.uom_po_id)
                #                 seller = procurement.product_id._select_seller(
                #                         partner_id=partner,
                #                         quantity=line.product_qty + procurement_uom_po_qty,
                #                         date=po.date_order and po.date_order[:10],
                #                         uom_id=procurement.product_id.uom_po_id)
                #
                #                 price_unit = self.env['account.tax']._fix_tax_included_price(seller.price,
                #                                                                              line.product_id.supplier_taxes_id,
                #                                                                              line.taxes_id) if seller else 0.0
                #                 if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
                #                     price_unit = seller.currency_id.compute(price_unit, po.currency_id)
                #
                #                 po_line = line.write({
                #                     'product_qty': line.product_qty + procurement_uom_po_qty,
                #                     'price_unit': price_unit,
                #                     'procurement_ids': [(4, procurement.id)]
                #                 })
