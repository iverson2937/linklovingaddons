# -*- coding: utf-8 -*-
import time

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class linkloving_product_multi_selection(models.Model):
    _name = 'll_pro_multi_sel.ll_pro_multi_sel'

    def create_order_by_active_model(self):
        if self._context.get('active_model') == 'purchase.order':
            self.create_purchase_order()
        elif self._context.get('active_model') == 'sale.order':
            self.create_sale_order()
        else:
            raise UserWarning("未找到对应的'active_model'")

    def create_sale_order(self):
        sale_order_obj = self.env['sale.order']
        # sale_order_obj.default_get(fields_list=[])
        order_id = self._context.get('order_id')
        new_order = sale_order_obj.browse(order_id)
        new_order.order_line = self.create_order_line(order_id)
        return {'type': 'ir.actions.act_window_close',
        }

    def create_order_line(self, order_id):
        sale_order = self.env['sale.order'].browse(order_id)

        sale_order_line_obj = self.env['sale.order.line']
        sale_lines = []
        for product_tmpl_id in self.product_ids:
            already_exist = False
            for line in sale_order.order_line:
                if line.product_id.product_tmpl_id == product_tmpl_id:
                    already_exist = True
            if not already_exist:
                so_line = sale_order_line_obj.create({
                   # 'name': product_id.name,
                    # 'price_unit': 0,
                    'product_uom_qty': 0.0,
                    'discount': 0.0,
                    'order_id': order_id,
                    'product_uom': product_tmpl_id.uom_id.id,
                    'product_id': product_tmpl_id.product_variant_id.id,
                    # 'tax_id': [(6, 0, product_id.taxes_id.ids)],
                })
                sale_lines.append(so_line.id)
        return sale_lines

    def create_purchase_order(self):
        pur_order_obj = self.env['purchase.order']
        order_id = self._context.get('order_id')
        new_order = pur_order_obj.browse(order_id)
        new_order.order_line = self.create_purchase_order_line(order_id)

        # sale_order_obj.default_get(fields_list=[])
        return {'type': 'ir.actions.act_window_close',
                }

    def create_purchase_order_line(self, order_id):
        pur_order_line_obj = self.env['purchase.order.line']
        pur_order = self.env['purchase.order'].browse(order_id)

        pur_lines = []
        for product_tmpl_id in self.product_ids:
            already_exist = False
            for line in pur_order.order_line:
                if line.product_id.product_tmpl_id == product_tmpl_id:
                    already_exist = True
            if not already_exist:
                # procurement_uom_po_qty = 0
                seller = product_tmpl_id.product_variant_id._select_seller(
                    # quantity=procurement_uom_po_qty,
                    uom_id=product_tmpl_id.uom_po_id)

                taxes = product_tmpl_id.product_variant_id.supplier_taxes_id
                # fpos = po.fiscal_position_id
                # taxes_id = fpos.map_tax(taxes) if fpos else taxes
                taxes_id = taxes
                if taxes_id:
                    taxes_id = taxes_id.filtered(lambda x: x.company_id.id == product_tmpl_id.company_id.id)

                price_unit = self.env['account.tax']._fix_tax_included_price(seller.price,
                                                                             product_tmpl_id.product_variant_id.supplier_taxes_id,
                                                                             taxes_id) if seller else 0.0
                # if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
                #     price_unit = seller.currency_id.compute(price_unit, po.currency_id)

                # product_lang = self.product_id.with_context({
                #     'lang': supplier.name.lang,
                #     'partner_id': supplier.name.id,
                # })
                # name = product_lang.display_name
                # if product_lang.description_purchase:
                #     name += '\n' + product_lang.description_purchase

                date_planned = self.env['purchase.order.line']._get_date_planned(seller,).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)

                po_line = pur_order_line_obj.create({
                    'name': product_tmpl_id.name,
                    'product_qty': 0,
                    'price_unit':price_unit,
                    'product_id': product_tmpl_id.product_variant_id.id,
                    'product_uom': product_tmpl_id.uom_po_id.id,
                    'price_unit': price_unit,
                    'date_planned': date_planned,
                    'taxes_id': [(6, 0, taxes_id.ids)],
                    # 'procurement_ids': [(4, self.id)],
                    'order_id': order_id,
                })
                pur_lines.append(po_line.id)
        return pur_lines

    product_ids = fields.Many2many('product.template', string='Products to make Order', )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)
    sale_ok = fields.Boolean()
    purchase_ok = fields.Boolean()
    
class SaleOrderDefaultGet(models.Model):
    _inherit = 'sale.order'
    
    def open_multi_product_select_window(self):
        order_lines = self.order_line
        product_ids = []
        for line in order_lines:
            product_ids.append(line.product_id.product_tmpl_id.id)
        return {'type': 'ir.actions.act_window',
                'res_model': 'll_pro_multi_sel.ll_pro_multi_sel',
                'view_mode': 'form',
                'context': '{"order_id":%s, "default_product_ids": %s,"sale_ok":True}' % (self.id, product_ids),
                # 'res_id': self.product_tmpl_id.id,
                'target': 'new'}
    
    @api.model
    def create(self, vals):
        # line_id_need_change = []
        # if vals.get('order_line'):
        #     for line in vals['order_line']:
        #         line_id_need_change.append(line[1])
        res = super(SaleOrderDefaultGet, self).create(vals)
        # line_need_change = self.env['sale.order.line'].browse(line_id_need_change)
        # for line in line_need_change:
        #     line.order_id = res.id
        return res


class PurchaseOrderDefaultGet(models.Model):
    _inherit = 'purchase.order'

    def open_multi_product_select_window(self):
        order_lines = self.order_line
        product_ids = []
        for line in order_lines:
            product_ids.append(line.product_id.product_tmpl_id.id)
        return {'type': 'ir.actions.act_window',
                'res_model': 'll_pro_multi_sel.ll_pro_multi_sel',
                'view_mode': 'form',
                'context': '{"order_id":%s, "default_product_ids": %s,"purchase_ok":True}' % (self.id, product_ids),
                # 'res_id': self.product_tmpl_id.id,
                'target': 'new'}


class ProductCategoryExtend(models.Model):
    _inherit = 'product.category'

    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                name = cat.name[0:16].encode('utf-8')
                if len(cat.name) > 16:
                    new_name = unicode(name + '...', 'utf-8')
                    res.append(new_name)
                else:
                    res.append(name)
                break
            return res

        name = [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]
        return name