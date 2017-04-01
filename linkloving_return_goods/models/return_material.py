# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare


class ReturnMaterial(models.Model):
    _name = 'return.goods'

    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    partner_invoice_id = fields.Many2one('res.partner', string=u'开票地址', readonly=False, required=False,
                                         help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner', string=u'退货地址', readonly=False, required=False,
                                          help="Delivery address for current sales order.")
    so_id = fields.Many2one('sale.order')
    tax_id = fields.Many2one('account.tax')
    picking_ids = fields.One2many('stock.picking', 'return_id')

    @api.multi
    def _compute_delivery_count(self):
        for order in self:
            order.delivery_count = len(order.picking_ids)

    delivery_count = fields.Integer(compute=_compute_delivery_count)
    date = fields.Date()
    remark = fields.Text(string=u'退货原因')
    tracking_number = fields.Char(string=u'物流信息')
    invoice_status = fields.Selection([
        ('to invoice', u'待对账'),
        ('no', u'待收货'),
        ('invoiced', u'已对账')
    ], string=u'对账状态', default='no')

    @api.depends('state', 'product_uom_qty', 'qty_delivered')
    def _compute_invoice_status(self):
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
        for line in self:
            if line.state not in ('sale', 'done'):
                line.invoice_status = 'no'
            elif True:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

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

    line_ids = fields.One2many('return.goods.line', 'return_id')
    state = fields.Selection([
        ('draft', u'草稿'),
        ('confirm', u'确认'),
        ('done', u'完成')
    ], default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('return.goods') or 'New'

        result = super(ReturnMaterial, self).create(vals)
        return result

    @api.multi
    def _prepare_invoice(self):
        inv_obj = self.env['account.invoice']
        account_id = False
        if self.partner_id.customer:
            account_id = self.partner_id.property_account_payable_id.id
        else:
            account_id = self.partner_id.property_income_payable_id.id
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.supplier_id.name,))

        invoice = inv_obj.create({
            'origin': self.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': account_id,
            'partner_id': self.partner_id.id,
            # 'partner_shipping_id': order.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'origin': self.name,
                'price_unit': self.unit_price,
                'account_id': 15,
                'quantity': self.qty_produced,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                # 'invoice_line_tax_ids': [(4, order.tax_id.id)],
                # 'account_analytic_id': order.project_id.id or False,
            })],
            # 'currency_id': order.pricelist_id.currency_id.id,
            # 'team_id': order.team_id.id,
            # 'comment': order.note,
        })
        # invoice.compute_taxes()
        # invoice.message_post_with_view('mail.message_origin_link',
        #             values={'self': invoice, 'origin': order},
        #             subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    @api.multi
    def return_confirm(self):
        picking_type = self.env.ref('stock.picking_type_in')

        picking_id = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id,
            'return_id': self.id,
            'location_id': self.partner_id.property_stock_customer.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': self.so_id.name if self.so_id else u'客户批量' + u'的退货',
            'tracking_number': self.tracking_number
        })
        for line in self.line_ids:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_id.uom_id.id,
                'return_line_id': line.id,
                'picking_id': picking_id.id,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id
            })
        picking_id.action_confirm()
        picking_id.force_assign()
        self.state = "confirm"


class ReturnMaterialLine(models.Model):
    _name = 'return.goods.line'
    return_id = fields.Many2one('return.goods')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True)
    product_uom_qty = fields.Float(string='Quantity', required=True,
                                   default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_id = fields.Many2one('account.tax')
    move_ids = fields.One2many('stock.move', 'return_line_id')

    invoice_status = fields.Selection([
        ('to invoice', u'待对账'),
        ('no', u'待收货'),
        ('invoiced', u'已对账')
    ], string=u'对账状态', default='no')

    @api.depends('state', 'product_uom_qty', 'qty_delivered')
    def _compute_invoice_status(self):
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
            if line.state not in ('sale', 'done'):
                line.invoice_status = 'no'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            elif all(move.state in ['done', 'cancel'] for move in line.move_ids):
                line.invoice_status = 'to invoice'
            else:
                line.invoice_status = 'no'

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * line.product_uom_qty

            line.update({
                'price_subtotal': price
            })

    price_subtotal = fields.Float(compute=_compute_amount, string=u'小计')

    @api.one
    def _get_qty_delivered(self):
        self.qty_delivered = sum(move.product_uom_qty for move in self.move_ids if move.state == 'done')

    qty_delivered = fields.Float(string='Delivered', copy=False, digits=dp.get_precision('Discount'),
                                 compute=_get_qty_delivered)

    @api.one
    def _get_qty_invoiced(self):
        self.invoiced = sum(
            invoice_line.product_uom_qty for invoice_line in self.invoice_line_ids if
            invoice_line.invoice_id.state != 'cancel')

    invoiced = fields.Float(string=u'已对账', copy=False, digits=dp.get_precision('Discount'),
                            compute=_get_qty_invoiced)
