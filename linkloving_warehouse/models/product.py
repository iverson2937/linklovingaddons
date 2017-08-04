# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It, MONK Software, Vauxoo
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume, Leonardo Donelli
#            Osval Reyes, Yanina Aular
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api
from odoo import fields, models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'
    area_id = fields.Many2one('stock.location.area', string='Area')
    location_x = fields.Char()
    location_y = fields.Char()

    product_specs = fields.Text(string=u'Product Specification', related='product_tmpl_id.product_specs')
    _sql_constraints = [
        ('default_code_uniq', 'unique (default_code)', _('Default Code already exist!')),
        # ('name_uniq', 'unique (name)', u'产品名称已存在!')
    ]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    reordering_min_qty = fields.Float(compute='_compute_nbr_reordering_rules', store=True,
                                      inverse='_set_nbr_reordering_rules')
    reordering_max_qty = fields.Float(compute='_compute_nbr_reordering_rules', store=True,
                                      inverse='_set_nbr_reordering_rules')
    last1_month_qty = fields.Float(string=u'上月销量')
    last2_month_qty = fields.Float(string=u'上上月销量')
    last3_month_qty = fields.Float(string=u'上上上月销量')

    def compute_sale_qty(self):
        products = f

    @api.multi
    def view_product_id(self):
        for product in self:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [[False, 'form']],
                'target': 'current',
                'res_id': product.id
            }

    @api.multi
    def _set_nbr_reordering_rules(self):
        pass
        # OrderPoint = self.env['stock.warehouse.orderpoint']
        # for product_tmplate in self:
        #     if product_tmplate.reordering_max_qty < product_tmplate.reordering_min_qty:
        #         raise UserError(u'最小数量不能大于最大数量')
        #
        #     orderpoint = OrderPoint.search([('product_id', '=', product_tmplate.product_variant_ids[0].id)])
        #     if not orderpoint:
        #         orderpoint.create({
        #             'product_id': product_tmplate.product_variant_ids[0].id,
        #             'product_max_qty': product_tmplate.reordering_max_qty if product_tmplate.reordering_max_qty else 0.0,
        #             'product_min_qty': product_tmplate.reordering_min_qty if product_tmplate.reordering_min_qty else 0.0,
        #         })
        #     elif len(orderpoint) > 1:
        #         raise UserError(u'有多条存货规则,请确认')
        #     elif len(orderpoint) == 1:
        #         orderpoint.product_max_qty = product_tmplate.reordering_max_qty
        #         orderpoint.product_min_qty = product_tmplate.reordering_min_qty

    def _compute_nbr_reordering_rules(self):
        res = {k: {'nbr_reordering_rules': 0, 'reordering_min_qty': 0, 'reordering_max_qty': 0} for k in self.ids}
        product_data = self.env['stock.warehouse.orderpoint'].read_group(
            [('product_id.product_tmpl_id', 'in', self.ids)], ['product_id', 'product_min_qty', 'product_max_qty'],
            ['product_id'])
        for data in product_data:
            product = self.env['product.product'].browse([data['product_id'][0]])
            product_tmpl_id = product.product_tmpl_id.id
            res[product_tmpl_id]['nbr_reordering_rules'] += int(data['product_id_count'])
            res[product_tmpl_id]['reordering_min_qty'] = data['product_min_qty']
            res[product_tmpl_id]['reordering_max_qty'] = data['product_max_qty']
        for template in self:
            template.nbr_reordering_rules = res[template.id]['nbr_reordering_rules']
            template.reordering_min_qty = res[template.id]['reordering_min_qty']
            template.reordering_max_qty = res[template.id]['reordering_max_qty']

    # @api.multi
    # def write(self, vals):
    #     if 'uom_id' in vals:
    #         new_uom = self.env['product.uom'].browse(vals['uom_id'])
    #         updated = self.filtered(lambda template: template.uom_id != new_uom)
    #         done_moves = self.env['stock.move'].search(
    #             [('product_id', 'in', updated.mapped('product_variant_ids').ids)])
    #         for move in done_moves:
    #             if move.state != 'done':
    #                 move.product_uom = vals['uom_id']
    #     return super(ProductTemplate, self).write(vals)

    def _get_default_uom_id(self):
        return self.env["product.uom"].search([], limit=1, order='id').id

    uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default Unit of Measure used for all stock operation.", track_visibility='onchange')

    product_specs = fields.Text(string=u'Product Specification')
    default_code = fields.Char(related='product_variant_ids.default_code')
    area_id = fields.Many2one(related='product_variant_ids.area_id', string='Area')
    location_x = fields.Char(related='product_variant_ids.location_x')
    location_y = fields.Char(related='product_variant_ids.location_y')
    name = fields.Char('Name', index=True, required=True, translate=False)
    _sql_constraints = [
        ('default_code_uniq1', 'unique (default_code)', _('Default Code already exist!')),
        # ('name_uniq', 'unique (name)', u'产品名称已存在!')
    ]

    # @api.multi
    # def write(self, vals):
    #     if 'uom_id' in vals:
    #         new_uom = self.env['product.uom'].browse(vals['uom_id'])
    #         updated = self.filtered(lambda template: template.uom_id != new_uom)
    #         done_moves = self.env['stock.move'].search(
    #             [('product_id', 'in', updated.mapped('product_variant_ids').ids)], limit=1)
    #
    #     return super(models.Model, self).write(vals)

    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        for record in self:

            record.active = not record.active
            active = not record.active
            products = self.env['product.product'].search(
                [('product_tmpl_id', '=', record.id), ('active', '=', active)])
            for product in products:
                product.active = not product.active
