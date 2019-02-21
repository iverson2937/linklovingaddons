# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare


class ReturnMaterial(models.Model):
    _name = 'return.goods'
    _order = 'create_date desc'

    name = fields.Char()
    partner_id = fields.Many2one('res.partner', states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    customer = fields.Boolean()
    supplier = fields.Boolean()
    partner_invoice_id = fields.Many2one('res.partner', string=u'开票地址',
                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                         required=False,
                                         help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner', string=u'退货地址', readonly=False, required=False,
                                          help="Delivery address for current sales order.",
                                          states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    so_id = fields.Many2one('sale.order', states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    purchase_id = fields.Many2one('purchase.order')
    tax_id = fields.Many2one('account.tax')
    picking_ids = fields.One2many('stock.picking', 'rma_id')
    invoice_ids = fields.One2many('account.invoice', compute='_get_invoiced')
    invoice_count = fields.Integer(compute='_get_invoiced')

    @api.multi
    def button_dummy(self):
        return True

    @api.multi
    def unlink(self):
        if self.state != 'draft':
            UserError(u'只可删除草稿状态的退货单')
        return super(ReturnMaterial, self).unlink()

    @api.onchange('tax_id')
    def onchange_tax_id(self):
        for line in self.line_ids:
            line.tax_id = self.tax_id.id

    @api.multi
    def _compute_delivery_count(self):
        for order in self:
            order.delivery_count = len(order.picking_ids)

    delivery_count = fields.Integer(compute=_compute_delivery_count)
    date = fields.Date(default=fields.date.today())
    remark = fields.Text(string=u'退货原因')
    tracking_number = fields.Char(string=u'物流信息')
    invoice_status = fields.Selection([
        ('to invoice', u'待对账'),
        ('no', u'待收货'),
        ('invoiced', u'已对账')
    ], string=u'对账状态', default='no', compute='_get_invoiced')
    amount_untaxed = fields.Monetary(string=u'未税金额', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string=u'税金', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')
    amount_total = fields.Monetary(string=u'总计', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')

    @api.model
    def _get_default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)

    @api.one
    @api.depends('line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = sum(line.price_subtotal for line in self.line_ids)
            amount_tax = sum(line.price_tax for line in self.line_ids)

            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('state', 'line_ids.invoice_status')
    def _get_invoiced(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the SO.
        """
        for order in self:
            invoice_ids = order.line_ids.mapped('invoice_lines').mapped('invoice_id')
            # Search for invoices which have been 'cancelled' (filter_refund = 'modify' in
            # 'account.invoice.refund')
            # use like as origin may contains multiple references (e.g. 'SO01, SO02')
            refunds = invoice_ids.search([('origin', 'like', order.name)])
            invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])
            # Search for refunds as well
            line_invoice_status = [line.invoice_status for line in order.line_ids]

            if line_invoice_status and all(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                invoice_status = 'invoiced'
            else:
                invoice_status = 'no'

            order.update({
                'invoice_count': len(set(invoice_ids.ids)),
                'invoice_ids': invoice_ids.ids,
                'invoice_status': invoice_status
            })

    @api.multi
    def action_view_invoice(self):
        return {
            'name': _('退货对账单'),
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': False,
            'res_model': 'account.invoice',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.invoice_ids.ids[0]
        }

    def action_view_delivery(self):

        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
            })
            return
        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        self.update(values)

    line_ids = fields.One2many('return.goods.line', 'rma_id')
    state = fields.Selection([
        ('draft', u'草稿'),
        ('confirm', u'确认'),
        ('order', u'退货单')
    ], default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if vals.get('customer'):
                vals['name'] = self.env['ir.sequence'].next_by_code('return.goods.customer') or 'New'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('return.goods.supplier') or 'New'

        result = super(ReturnMaterial, self).create(vals)
        return result

    @api.multi
    def create_invoice(self):

        self.action_invoice_create()

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the rma.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            for line in order.line_ids.sorted(key=lambda l: l.qty_to_invoice < 0):
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                elif group_key in invoices:
                    vals = {}
                    if order.name not in invoices[group_key].origin.split(', '):
                        vals['origin'] = invoices[group_key].origin + ', ' + order.name
                    if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(', '):
                        vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                    invoices[group_key].write(vals)
                if line.qty_to_invoice > 0:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                elif line.qty_to_invoice < 0 and final:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoice] = references[invoice] | order
            for invoice in invoices.values():
                if not invoice.invoice_line_ids:
                    raise UserError(_('There is no invoicable line.'))
                # If invoice is negative, do a refund invoice instead
                if invoice.amount_untaxed < 0:
                    invoice.type = 'out_refund'
                    for line in invoice.invoice_line_ids:
                        line.quantity = -line.quantity
                # Use additional field helper function (for account extensions)
                for line in invoice.invoice_line_ids:
                    line._set_additional_fields(invoice)
                # Necessary to force computation of taxes. In account_invoice, they are triggered
                # by onchanges, which are not triggered when doing a create.
                invoice.compute_taxes()
                invoice.message_post_with_view('mail.message_origin_link',
                                               values={'self': invoice, 'origin': references[invoice]},
                                               subtype_id=self.env.ref('mail.mt_note').id)
            return [inv.id for inv in invoices.values()]

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        if self.customer:
            invoice_type = 'out_refund'
            account_id = self.partner_invoice_id.property_account_receivable_id.id,
        else:
            invoice_type = 'in_refund'
            account_id = self.partner_invoice_id.property_account_payable_id.id,
        invoice_vals = {
            'name': '',
            'origin': self.name,
            'type': invoice_type,
            'account_id': account_id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
        }
        return invoice_vals

    def write(self, vals):
        if vals.get('tracking_number'):
            for line in self.line_ids:
                for move in line.move_ids:
                    move.picking_id.tracking_number = vals.get('tracking_number')
        return super(ReturnMaterial, self).write(vals)

    @api.multi
    def return_confirm(self):
        if not self.line_ids:
            raise UserError(u'至少含有一条退货明细')
        if self.customer:
            picking_type = self.env.ref('stock.picking_type_in')
            origin = self.so_id.name if self.so_id else u'客户批量的退货'
            location_id = self.partner_id.property_stock_customer.id,
            location_dest_id = picking_type.default_location_dest_id.id,
        else:
            picking_type = self.env.ref('stock.picking_type_out')
            origin = self.purchase_id.name if self.so_id else u'批量退货供应商'
            location_id = picking_type.default_location_src_id.id,
            location_dest_id = self.partner_id.property_stock_supplier.id
        print location_dest_id, ''''ddd'''


        picking_id = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id,
            'rma_id': self.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'origin': origin,
            'tracking_number': self.tracking_number if self.tracking_number else ''
        })
        for line in self.line_ids:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_id.uom_id.id,
                'rma_line_id': line.id,
                'origin': origin,
                'quantity_adjusted_qty': line.product_id.qty_available + line.product_uom_qty if order_type == 'sell_return' else line.product_id.qty_available - line.product_uom_qty,
                'picking_id': picking_id.id,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id
            })
        picking_id.action_confirm()
        picking_id.force_assign()
        self.state = "order"


class ReturnMaterialLine(models.Model):
    _name = 'return.goods.line'
    rma_id = fields.Many2one('return.goods', on_delete="cascade")
    product_id = fields.Many2one('product.product', string='Product',
                                 change_default=True, ondelete='restrict', required=True)
    product_uom_qty = fields.Float(string='Quantity', required=True,
                                   default=1.0)

    currency_id = fields.Many2one('res.currency', related='rma_id.currency_id')
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_id = fields.Many2one('account.tax')
    move_ids = fields.One2many('stock.move', 'rma_line_id')
    invoice_lines = fields.One2many('account.invoice.line', 'rma_line_id')
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    tax_id = fields.Many2one('account.tax')

    @api.depends('product_uom_qty', 'price_unit', 'tax_id')
    @api.multi
    def _compute_amount(self):
        """
        Compute the amounts of the rma line.
        """
        for line in self:
            line.update({
                'price_tax': line.product_uom_qty * line.price_unit * line.tax_id.amount / 100,
                'price_total': line.price_unit * line.product_uom_qty,
                'price_subtotal': line.price_unit * (1 - line.tax_id.amount / 100) * line.product_uom_qty,

            })

    invoice_status = fields.Selection([
        ('to invoice', u'待对账'),
        ('no', u'待收货'),
        ('invoiced', u'已对账')
    ], string=u'对账状态', compute='_compute_invoice_status', store=True, readonly=True, default='no')

    @api.depends('product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):

        """
        TBD

        """

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:

            if float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            elif line.qty_to_invoice and not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            else:
                line.invoice_status = 'no'

    price_subtotal = fields.Float(compute=_compute_amount, string=u'小计')

    @api.one
    def _get_qty_delivered(self):
        self.qty_delivered = sum(move.product_uom_qty for move in self.move_ids if move.state == 'done')
        print self.qty_delivered

    qty_delivered = fields.Float(string='Delivered', copy=False, digits=dp.get_precision('Product Unit of Measure'),
                                 readonly=True)

    @api.one
    def _get_qty_invoiced(self):
        self.invoiced = sum(
            invoice_line.product_uom_qty for invoice_line in self.invoice_line_ids if
            invoice_line.invoice_id.state != 'cancel')

    qty_to_invoice = fields.Float(
        compute='_get_to_invoice_qty', string='待对账数量', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
    qty_invoiced = fields.Float(
        compute='_get_invoice_qty', string='Invoiced', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'rma_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            line.qty_to_invoice = line.qty_delivered - line.qty_invoiced

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    qty_invoiced += invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom)

            line.qty_invoiced = qty_invoiced

    @api.onchange('product_id')
    def on_change_product_id(self):
        print self.product_id.uom_id
        self.product_uom = self.product_id.uom_id.id
        self.tax_id = self.rma_id.tax_id

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).

        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'rma_line_id': line.id})
                self.env['account.invoice.line'].create(vals)

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        if self.rma_id.customer:
            account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        else:
            account = self.product_id.property_account_expense_id or self.product_id.categ_id.property_account_expense_categ_id

        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        res = {
            'name': self.product_id.name,
            'origin': self.rma_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(4, self.tax_id.id)]

        }
        return res

    @api.model
    def default_get(self, fields):
        res = super(ReturnMaterialLine, self).default_get(fields)
        return res
