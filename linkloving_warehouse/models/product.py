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
    @api.multi
    def write(self, vals):
        if 'uom_id' in vals:
            new_uom = self.env['product.uom'].browse(vals['uom_id'])
            updated = self.filtered(lambda template: template.uom_id != new_uom)
            done_moves = self.env['stock.move'].search([('product_id', 'in', updated.mapped('product_variant_ids').ids)], limit=1)

        return super(models.Model, self).write(vals)
