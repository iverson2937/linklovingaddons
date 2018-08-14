# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_is_zero, float_compare
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
    handle_date = fields.Datetime(string=u'交期')
    product_id = fields.Many2one(related='order_line.product_id')
    product_qty = fields.Float(related='order_line.product_qty')
    invoiced_amount = fields.Float(compute='_compute_invoice_amount')
    remaining_amount = fields.Float(compute='_compute_invoice_amount')
    shipped_amount = fields.Float(compute='_compute_invoice_amount')
    pre_payment_amount = fields.Float(compute='_compute_invoice_amount')

    @api.multi
    def button_confirm(self):
        for order in self:
            for line in order.order_line:
                print line.product_id.status, 'dd'
                if line.product_id.status == 'eol' or not line.product_id.active:
                    raise UserError('%s已停产或者归档,不能下单购买' % line.product_id.name)

        res = super(PurchaseOrder, self).button_confirm()

        return res

    @api.multi
    def button_cancel(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state in ['qc_check', 'validate', 'picking', 'waiting_in', 'done']:
                    raise UserError(u'不能取消已经收到货的订单: %s.' % (order.name))
        return super(PurchaseOrder, self).button_cancel()

    @api.multi
    @api.depends('invoice_ids')
    def _compute_invoice_amount(self):
        for order in self:
            invoiced_amount = remaining_amount = shipped_amount = 0.0
            for line in order.order_line:
                if line.product_id.type in ['consu', 'product']:
                    shipped_amount += line.qty_received * line.price_unit
                else:
                    shipped_amount += line.product_qty * line.price_unit
            for invoice in order.invoice_ids.filtered(lambda x: x.state not in ['draft', 'post']):
                sign = invoice.type in ['in_refund', 'out_refund'] and -1 or 1
                invoiced_amount += invoice.amount_total * sign
                remaining_amount += invoice.residual
            order.invoiced_amount = invoiced_amount
            order.remaining_amount = remaining_amount
            order.shipped_amount = shipped_amount
            order.pre_payment_amount = 0.0
            if order.invoice_status == 'no' and order.shipping_rate < 10:
                order.pre_payment_amount = invoiced_amount
            else:
                order.invoiced_amount = invoiced_amount

    @api.depends('product_count', 'order_line.qty_received', 'state')
    def _compute_shipping_rate(self):
        for r in self:
            if r.product_count and r.state == 'purchase':
                qtys = sum(line.qty_received for line in r.order_line)
                r.shipping_rate = (qtys / r.product_count) * 100.0
            if r.is_shipped:
                r.shipping_rate = 100.0

    shipping_rate = fields.Float(string=u"收货率", compute='_compute_shipping_rate', store=True)

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_is_shipped(self):
        for order in self:
            if order.picking_ids and all([x.state in ('done', 'cancel', 'waiting_in') for x in order.picking_ids]):
                order.is_shipped = True

    @api.multi
    def _compute_shipping_status(self):
        for order in self:

            if order.state == 'purchase' and all(
                    picking.state in ["cancel", "done", "waiting_in"] for picking in order.picking_ids):
                order.shipping_status = 'done'
            elif order.state == 'purchase ' and any(
                    picking.state in ["cancel", "done", "waiting_in"] for picking in order.picking_ids):
                order.shipping_status = 'part_shipping'
            else:
                order.shipping_status = 'no'

    invoice_status = fields.Selection([
        ('no', u'待出货'),
        ('to invoice', u'待对账'),
        ('invoiced', u'已对账完成'),
    ], string=u'对账单状态', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')

    @api.depends('state', 'order_line.qty_invoiced', 'order_line.qty_received', 'order_line.product_qty')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.invoice_status = 'no'
                continue

            if any(float_compare(line.qty_invoiced,
                                 line.product_qty if line.product_id.purchase_method == 'purchase' else line.qty_received,
                                 precision_digits=precision) == -1 for line in order.order_line):
                order.invoice_status = 'to invoice'
            elif all(float_compare(line.qty_invoiced,
                                   line.product_qty if line.product_id.purchase_method == 'purchase' else line.qty_received,
                                   precision_digits=precision) >= 0 for line in order.order_line) and order.invoice_ids:
                order.invoice_status = 'invoiced'
            # elif all(float_compare(line.qty_invoiced,
            #                        line.qty_received if line.product_id.purchase_method == 'purchase' else line.qty_received,
            #                        precision_digits=precision) >= 0 for line in
            #          order.order_line) and order.invoice_ids and not order.picking_ids.filtered(
            #     lambda picking_id: picking_id.state not in ('cancel', 'done')):
            #     order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'

    shipping_status = fields.Selection([
        ('no', u'未入库'),
        ('part_shipping', u'部分入库'),
        ('done', u'入库完成'),
    ], compute='_compute_shipping_status', default='no')

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
                if line.product_id.type != 'service':
                    count += line.product_qty
            order.product_count = count

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }

    @api.multi
    def button_done(self):
        for pick in self.picking_ids.filtered(lambda r: r.state not in ('cancel', 'done')):
            pick.action_cancel()
        self.write({'state': 'done', 'is_shipped': True})


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_specs = fields.Text(string=u'Specification', related='product_id.product_specs')
    shipping_status = fields.Selection([
        ('no', u'待出货'),
        ('part_shipping', u'部分出货'),
        ('done', u'出货完成'),
    ], default='no', compute='_compute_shipping_status', store=True, readonly=True)

    @api.multi
    def _compute_to_ship_qty(self):
        for line in self:
            line.to_ship_qty = line.product_qty - line.qty_received

    to_ship_qty = fields.Float(compute=_compute_to_ship_qty, string='欠货数量')

    @api.depends('product_qty', 'qty_received', 'qty_to_invoice', 'qty_invoiced')
    def _compute_shipping_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:

            if float_is_zero(line.qty_received, precision_digits=precision) and line.product_id.type in (
                    'consu', 'product'):
                line.shipping_status = 'no'
            elif float_compare(line.qty_received, line.product_qty,
                               precision_digits=precision) < 0 and line.product_id.type in ('consu', 'product'):
                line.shipping_status = 'part_shipping'

            elif float_compare(line.qty_received, line.product_qty,
                               precision_digits=precision) == 0 and line.product_id.type in (
                    'consu', 'product'):
                line.shipping_status = 'done'

            else:
                line.shipping_status = 'no'

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
        ('no', u'没有要对账的'),
        ('to invoice', u'待对账'),
        ('invoiced', u'已对账完成'),
    ], string=u'对账单状态', readonly=True, copy=False, default='no')

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            if line.product_id.type not in ['product', 'consu']:
                continue
            qty = 0.0
            price_unit = line._get_stock_move_price_unit()
            for move in line.move_ids.filtered(lambda x: x.state != 'cancel'):
                qty += move.product_qty
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'date': line.order_id.date_order,
                'date_expected': line.date_planned,
                'location_id': line.order_id.partner_id.property_stock_supplier.id,
                'location_dest_id': line.order_id._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': line.order_id.dest_address_id.id,
                'move_dest_id': False,
                'state': 'draft',
                'purchase_line_id': line.id,
                'company_id': line.order_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': line.order_id.picking_type_id.id,
                'group_id': line.order_id.group_id.id,
                'procurement_id': False,
                'origin': line.order_id.name,
                'route_ids': line.order_id.picking_type_id.warehouse_id and [
                    (6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id': line.order_id.picking_type_id.warehouse_id.id,
                'move_order_type': 'procurement_warehousing',
                'quantity_adjusted_qty': line.product_id.qty_available + line.product_qty,
            }
            # Fullfill all related procurements with this po line
            diff_quantity = line.product_qty - qty
            for procurement in line.procurement_ids:
                # If the procurement has some moves already, we should deduct their quantity
                sum_existing_moves = sum(x.product_qty for x in procurement.move_ids if x.state != 'cancel')
                existing_proc_qty = procurement.product_id.uom_id._compute_quantity(sum_existing_moves,
                                                                                    procurement.product_uom)
                procurement_qty = procurement.product_uom._compute_quantity(procurement.product_qty,
                                                                            line.product_uom) - existing_proc_qty
                if float_compare(procurement_qty, 0.0,
                                 precision_rounding=procurement.product_uom.rounding) > 0 and float_compare(
                    diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                    tmp = template.copy()
                    tmp.update({
                        'product_uom_qty': min(procurement_qty, diff_quantity),
                        'move_dest_id': procurement.move_dest_id.id,
                        # move destination is same as procurement destination
                        'procurement_id': procurement.id,
                        'propagate': procurement.rule_id.propagate,
                    })
                    done += moves.create(tmp)
                    diff_quantity -= min(procurement_qty, diff_quantity)
            if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                template['product_uom_qty'] = diff_quantity
                done += moves.create(template)
        return done

    # 重写变更价格条件,只有在产品变更的时候再找价格
    @api.onchange('product_id')
    def _onchange_quantity(self):
        if not self.product_id:
            return

        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                             seller.tax_id,
                                                                             self.taxes_id,
                                                                             self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        self.price_unit = price_unit


class manual_combine_po(models.TransientModel):
    _name = "manual.combine.po"

    @api.one
    def action_confirm(self):
        ids = self._context.get("active_ids")
        pos = self.env[self._context.get("active_model")].search([("id", "in", ids)])
        min_handle_date = min(po.handle_date for po in pos)
        if any(po.state not in ['make_by_mrp', 'draft'] for po in pos):
            raise UserError(u'只能合并草稿状态的采购单')
        if len(pos.mapped("partner_id").ids) != 1:  # 如果相等 代表不重复
            raise UserError("请选择相同供应商的采购单进行合并.")
        else:
            po_first = pos[0]
            po_first.handle_date = min_handle_date
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
        if not po.origin or not po_to_combine.origin:
            return
        po_to_combine_split = po_to_combine.origin.split(', ')
        po_split = po.origin.split(', ')
        combined_origin_set = set(po_split + po_to_combine_split)
        combined_origin = ''
        for o in combined_origin_set:
            combined_origin += o + ', '
        combined_origin = combined_origin[:len(combined_origin) - 2]

        po.write({'origin': combined_origin})
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


class PurchaseReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        # TDE FIXME: store it in the wizard, stupid
        picking = self.env['stock.picking'].browse(self.env.context['active_id'])

        return_moves = self.product_return_moves.mapped('move_id')
        unreserve_moves = self.env['stock.move']
        for move in return_moves:
            to_check_moves = self.env['stock.move'] | move.move_dest_id
            while to_check_moves:
                current_move = to_check_moves[-1]
                to_check_moves = to_check_moves[:-1]
                if current_move.state not in ('done', 'cancel') and current_move.reserved_quant_ids:
                    unreserve_moves |= current_move
                split_move_ids = self.env['stock.move'].search([('split_from', '=', current_move.id)])
                to_check_moves |= split_move_ids

        if unreserve_moves:
            unreserve_moves.do_unreserve()
            # break the link between moves in order to be able to fix them later if needed
            unreserve_moves.write({'move_orig_ids': False})

        # create new picking for returned products
        picking_type_id = picking.picking_type_id.return_picking_type_id.id or picking.picking_type_id.id
        new_picking = picking.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': picking.name,
            'location_id': picking.location_dest_id.id,
            'location_dest_id': self.location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': new_picking, 'origin': picking},
                                           subtype_id=self.env.ref('mail.mt_note').id)

        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed"))
            new_qty = return_line.quantity
            if new_qty:
                # The return of a return should be linked with the original's destination move if it was not cancelled
                if return_line.move_id.origin_returned_move_id.move_dest_id.id and return_line.move_id.origin_returned_move_id.move_dest_id.state != 'cancel':
                    move_dest_id = return_line.move_id.origin_returned_move_id.move_dest_id.id
                else:
                    move_dest_id = False

                returned_lines += 1
                return_line.move_id.copy({
                    'product_id': return_line.product_id.id,
                    'product_uom_qty': new_qty,
                    'picking_id': new_picking.id,
                    'state': 'draft',
                    'move_order_type': 'purchase_return',
                    'location_id': return_line.move_id.location_dest_id.id,
                    'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
                    'picking_type_id': picking_type_id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                    'origin_returned_move_id': return_line.move_id.id,
                    'procure_method': 'make_to_stock',
                    'move_dest_id': move_dest_id,
                })

        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _fix_tax_included_price_company(self, price, prod_taxes, line_taxes, company_id):
        if company_id:
            # To keep the same behavior as in _compute_tax_id
            prod_taxes = prod_taxes.filtered(lambda tax: tax.company_id == company_id)
            line_taxes = line_taxes.filtered(lambda tax: tax.company_id == company_id)
        return self._fix_tax_included_price(price, prod_taxes, line_taxes)
