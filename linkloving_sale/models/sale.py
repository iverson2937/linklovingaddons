# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, SUPERUSER_ID
from itertools import groupby

from odoo.tools import float_compare, float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    """

    """""

    _inherit = 'sale.order'
    tax_id = fields.Many2one('account.tax')
    product_count = fields.Float(compute='get_product_count')
    invoiced_amount = fields.Float(compute='_compute_invoice_amount')
    remaining_amount = fields.Float(compute='_compute_invoice_amount')
    shipped_amount = fields.Float(compute='_compute_invoice_amount')
    pre_payment_amount = fields.Float(compute='_compute_invoice_amount')

    # 重新计算收货数量由于出入库bug临时使用
    def recompute_receive_amount(self):
        for line in self.order_line:
            line.qty_delivered = line.product_uom_qty

    @api.multi
    @api.depends('invoice_ids')
    def _compute_invoice_amount(self):
        for order in self:
            invoiced_amount = remaining_amount = shipped_amount = 0.0
            for line in order.order_line:
                if line.product_id.type in ['consu', 'product']:
                    shipped_amount += line.qty_delivered * line.product_id.standard_price
                else:
                    shipped_amount += line.product_uom_qty * line.price_unit
            for invoice in order.invoice_ids:
                invoiced_amount += invoice.amount_total
                remaining_amount += invoice.residual

            order.remaining_amount = remaining_amount
            order.shipped_amount = shipped_amount
            order.pre_payment_amount = 0.0
            if order.invoice_status == 'no' and order.shipping_rate < 10:
                order.pre_payment_amount = invoiced_amount
            else:
                order.invoiced_amount = invoiced_amount

    @api.depends('product_count', 'order_line.qty_delivered')
    def _compute_shipping_rate(self):
        for r in self:
            if r.product_count:
                qtys = sum(line.qty_delivered for line in r.order_line)
                r.shipping_rate = (qtys / r.product_count) * 100.0

    shipping_rate = fields.Float(string=u"出货率", compute='_compute_shipping_rate', store=True)
    pi_number = fields.Char(string='PI Number')
    is_emergency = fields.Boolean(string=u'Is Emergency')
    remark = fields.Text(string=u'备注')

    @api.onchange('is_emergency')
    def onchange_is_emergency(self):
        for picking_id in self.picking_ids:
            picking_id.write({'is_emergency': self.is_emergency})

    def get_product_count(self):
        for order in self:
            count = 0.0
            for line in order.order_line:
                if line.product_id.type in ['product', 'consu']:
                    qty = line.product_uom_qty
                else:
                    qty = 0
                count += qty
            order.product_count = count

    @api.multi
    def action_done(self):
        for order in self:
            for pick in order.picking_ids.filtered(lambda r: r.state not in ('cancel', 'done')):
                pick.action_cancel()
            order.write({'state': 'done', 'shipping_status': 'done', 'shipping_rate': 100.0})

    @api.multi
    def button_cancel_sale_order(self):
        for order in self:
            order.state = 'sale'
            order._compute_shipping_rate()

    @api.multi
    def button_dummy(self):
        self.mapped('order_line')._compute_amount()

    @api.multi
    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        self.mapped('order_line')._compute_amount()
        # FIXME: allen why first tim not worker properly
        self.mapped('order_line')._compute_amount()
        return result

    invoice_status = fields.Selection([
        ('upselling', u'超售商机'),
        ('invoiced', u'已对账完成'),
        ('to invoice', u'待对账'),
        ('no', u'没有要对账的')
    ], string=u'对账单状态', compute='_get_invoiced', store=True, readonly=True)
    shipping_status = fields.Selection([
        ('no', u'待出货'),
        ('part_shipping', u'部分出货'),
        ('done', u'出货完成'),
    ], compute='_get_shipping_status', default='no', store=True)

    @api.one
    @api.depends('order_line.shipping_status')
    def _get_shipping_status(self):
        for order in self:

            if order.state == 'sale' and all(line.shipping_status == 'done' for line in self.order_line):
                order.shipping_status = 'done'
            elif order.state == 'sale' and any(line.shipping_status == 'part_shipping' for line in self.order_line):
                order.shipping_status = 'part_shipping'
            else:
                order.shipping_status = 'no'

    @api.multi
    def order_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        for category, lines in groupby(self.order_line, lambda l: l.layout_category_id):
            # If last added category induced a pagebreak, this one will be on a new page
            if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
                report_pages.append([])
            # Append category to current report page
            report_pages[-1].append({
                'name': category and category.name or 'Uncategorized',
                'subtotal': category and category.subtotal,
                'pagebreak': category and category.pagebreak,
                'lines': list(lines),
                'is_domestic': self.team_id.is_domestic if self.team_id else False
            })

        return report_pages

    question_record_count = fields.Integer(string=u'问题记录')
    inspection_report_count = fields.Integer(string=u'验货报告')

    @api.multi
    def action_view_question(self):
        action = self.env.ref('mail.action_view_mail_message').read()[0]
        # action = self.env.ref('crm.crm_action_view_mail_message').read()[0]

        pickings = self.mapped('message_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids), ('sale_order_type', '=', self._context['sale_type'])]
        return action


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_specs = fields.Text(string=u'Product Specification', related='product_id.product_specs')
    inner_spec = fields.Char(related='product_id.inner_spec')
    inner_code = fields.Char(related='product_id.inner_code')
    price_subtotal = fields.Monetary(string='Subtotal', readonly=True, store=True, compute=None)
    price_tax = fields.Monetary(string='Taxes', readonly=True, store=True, compute=None)
    price_total = fields.Monetary(string='Total', readonly=True, store=True, compute=None)
    qty_available = fields.Float(string=u'库存', related='product_id.qty_available')
    validity_date = fields.Date(string=u'交货日期', related='order_id.validity_date', store=True)
    pi_number = fields.Char(related='order_id.pi_number')
    remark = fields.Text(string='备注')

    # FIXME:allen  how to remove this
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(self.product_id.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    return {}
        return {}

    invoice_status = fields.Selection([
        ('upselling', u'超售商机'),
        ('invoiced', u'已对账完成'),
        ('to invoice', u'待对账'),
        ('no', u'未发货')
    ], string=u'对账单状态', compute='_compute_invoice_status', store=True, readonly=True, default='no')
    shipping_status = fields.Selection([
        ('no', u'待出货'),
        ('part_shipping', u'部分出货'),
        ('done', u'出货完成'),
    ], default='no', compute='_compute_shipping_status', store=True, readonly=True)

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
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

            if float_is_zero(line.qty_delivered, precision_digits=precision) and line.product_id.type in (
                    'consu', 'product'):
                line.shipping_status = 'no'
            elif float_compare(line.qty_delivered, line.product_uom_qty,
                               precision_digits=precision) < 0 and line.product_id.type in ('consu', 'product'):
                line.shipping_status = 'part_shipping'

            elif float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 0:
                line.shipping_status = 'done'
            elif line.product_id.type not in ('consu', 'product'):
                line.shipping_status = 'done'
            else:
                line.shipping_status = 'no'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
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
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision) and line.product_id.type in (
                    'consu', 'product'):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'


class SaleProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _get_stock_move_values(self):
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        group_id = False
        if self.rule_id.group_propagation_option == 'propagate':
            group_id = self.group_id.id
        elif self.rule_id.group_propagation_option == 'fixed':
            group_id = self.rule_id.group_id.id
        date_expected = (datetime.strptime(self.date_planned, DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(
            days=self.rule_id.delay or 0)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        qty_done = sum(self.move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))
        qty_left = max(self.product_qty - qty_done, 0)
        return {
            'name': self.name,
            'company_id': self.rule_id.company_id.id or self.rule_id.location_src_id.company_id.id or self.rule_id.location_id.company_id.id or self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': self.rule_id.partner_address_id.id or (
                    self.group_id and self.group_id.partner_id.id) or False,
            'location_id': self.rule_id.location_src_id.id,
            'location_dest_id': self.location_id.id,
            'move_dest_id': self.move_dest_id and self.move_dest_id.id or False,
            'procurement_id': self.id,
            'rule_id': self.rule_id.id,
            'procure_method': self.rule_id.procure_method,
            'origin': self.origin,
            'picking_type_id': self.rule_id.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in self.route_ids],
            'warehouse_id': self.rule_id.propagate_warehouse_id.id or self.rule_id.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate': self.rule_id.propagate,
            'priority': self.priority,
            'move_order_type': 'sell_out',
            'quantity_adjusted_qty': self.product_id.qty_available - qty_left
        }
