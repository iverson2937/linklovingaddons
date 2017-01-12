# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, SUPERUSER_ID
from itertools import groupby


class SaleOrder(models.Model):
    """

    """""

    _inherit = 'sale.order'
    tax_id = fields.Many2one('account.tax', required=True)
    product_count = fields.Float(compute='get_product_count')
    pi_number = fields.Char(string='PI Number')

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
        print report_pages

        return report_pages


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_specs = fields.Text(string=u'产品规格', related='product_id.product_specs')
    inner_spec = fields.Char(related='product_id.inner_spec', string=u'国内型号')
    inner_code = fields.Char(related='product_id.inner_code', string=u'国内简称')
    price_subtotal = fields.Monetary(string='Subtotal', readonly=True, store=True, compute=None)
    price_tax = fields.Monetary(string='Taxes', readonly=True, store=True, compute=None)
    price_total = fields.Monetary(string='Total', readonly=True, store=True, compute=None)
