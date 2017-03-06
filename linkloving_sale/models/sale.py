# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, SUPERUSER_ID
from itertools import groupby

from odoo.tools import float_compare


class SaleOrder(models.Model):
    """

    """""

    _inherit = 'sale.order'
    tax_id = fields.Many2one('account.tax', required=True)
    product_count = fields.Float(compute='get_product_count')
    pi_number = fields.Char(string='PI Number')
    is_emergency = fields.Boolean(string=u'Is Emergency')

    @api.onchange('is_emergency')
    def onchange_is_emergency(self):
        for picking_id in self.picking_ids:
            picking_id.write({'is_emergency': self.is_emergency})

    def get_product_count(self):
        count = 0.0
        for line in self.order_line:
            count += line.product_uom_qty
        self.product_count = count

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


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_specs = fields.Text(string=u'Product Specification', related='product_id.product_specs')
    inner_spec = fields.Char(related='product_id.inner_spec')
    inner_code = fields.Char(related='product_id.inner_code')
    price_subtotal = fields.Monetary(string='Subtotal', readonly=True, store=True, compute=None)
    price_tax = fields.Monetary(string='Taxes', readonly=True, store=True, compute=None)
    price_total = fields.Monetary(string='Total', readonly=True, store=True, compute=None)

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
