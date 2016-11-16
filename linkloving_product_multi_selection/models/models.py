# -*- coding: utf-8 -*-
import time

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class linkloving_product_multi_selection(models.Model):
    _name = 'll_pro_multi_sel.ll_pro_multi_sel'


    @api.model
    def create(self, vals):
        return super(linkloving_product_multi_selection, self).create(vals)
    @api.model
    def _count(self):
        return len(self._context.get('active_ids', []))

    @api.onchange('product_ids')
    def onchange_product_id(self, product_ids):
        print 'change'
    # def test(self):
    #     print '123'
    # @api.model
    # def default_get(self, fields_list):
        # pro_multi_sel = self.env['ll_pro_multi_sel.ll_pro_multi_sel'].search([('user_id', '=', self.env.user.id)])
        # choose_active_ids = self._context.get('active_ids')
        # #如果已经存在了记录
        # if pro_multi_sel:
        #     new_active_ids = list(set(choose_active_ids).difference(set(pro_multi_sel.orign_active_ids)))
        #     pro_multi_sel.orign_active_ids = (4, [new_active_ids])
        #     pro_multi_sel.product_ids = (4, [self.env['product.template'].browse(new_active_ids)])
        #     pro_multi_sel.count = len(pro_multi_sel.orign_active_ids)
        # else:
        #     self.env['ll_pro_multi_sel.ll_pro_multi_sel'].create({'user_id':self.env.user.id,
        #                         'orign_active_ids':choose_active_ids,
        #                         'product_ids':[self.env['product.template'].browse(choose_active_ids)],
        #                         'count':len(choose_active_ids)
        #   })
    @api.model
    def write(self, vals):
        return super(linkloving_product_multi_selection, self).write(vals)
    @api.model
    def _default_products_id(self):
            product_obj = self.env['product.template']
            project_lines = product_obj.browse(self._context.get('active_ids'))
            # orign_lines = self.env['ll_pro_multi_sel.ll_pro_multi_sel'].search(['user_id', '=', self.env.user.id])
            # if not orign_lines:
            #     pass
            # else:
            #     choose_ids = self._context.get('active_ids')
            #     for product_id in choose_ids:
            #         for line in orign_lines:
            #             if line.id == product_id:
            #                 break
            return project_lines

    def create_sale_order(self):
        sale_order_obj = self.env['sale.order']
        # sale_order_obj.default_get(fields_list=[])
        return {'type': 'ir.actions.act_window',
         'res_model': 'sale.order',
         'view_mode': 'form',
         # 'res_id': self.product_tmpl_id.id,
        'context': {'default_order_line': self.create_order_line()} ,
        'target': 'current'}

    def create_order_line(self):
        sale_order_line_obj = self.env['sale.order.line']
        sale_lines = []
        for product_tmpl_id in self.product_ids:
            so_line = sale_order_line_obj.create({
                # 'name': product_id.name,
                # 'price_unit': 0,
                'product_uom_qty': 0.0,
                'discount': 0.0,
                'order_id': 1,
                # 'product_uom': product_tmpl_id.uom_id.id,
                'product_id': product_tmpl_id.product_variant_id.id,
                # 'tax_id': [(6, 0, product_id.taxes_id.ids)],
            })
            sale_lines.append(so_line.id)
        return sale_lines
    def create_purchase_order(self):
        pur_order_obj = self.env['purchase.order']
        # sale_order_obj.default_get(fields_list=[])
        return {'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                # 'res_id': self.product_tmpl_id.id,
                'context': {'default_order_line': self.create_purchase_order_line()},
                'target': 'current'}
        print 'purchase'

    def create_purchase_order_line(self):
        pur_order_line_obj = self.env['purchase.order.line']
        pur_lines = []
        for product_tmpl_id in self.product_ids:
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
                'order_id': 1,
            })
            pur_lines.append(po_line.id)
        return pur_lines
    count = fields.Integer(computed=_count, string='# of Products')
    product_ids = fields.Many2many('product.template', string='Products to make Order',
                                 default=_default_products_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)

    orign_active_ids = fields.Char('Orign active ids',)
    
    
class SaleOrderDefaultGet(models.Model):
    _inherit = 'sale.order'
    
    
    @api.model
    def default_get(self, fields_list):
        return super(SaleOrderDefaultGet, self).default_get(fields_list)
    
    @api.model
    def create(self, vals):
        line_id_need_change = []
        if vals.get('order_line'):
            for line in vals['order_line']:
                line_id_need_change.append(line[1])
        res = super(SaleOrderDefaultGet, self).create(vals)
        line_need_change = self.env['sale.order.line'].browse(line_id_need_change)
        for line in line_need_change:
            line.order_id = res.id
        return res


class PurchaseOrderDefaultGet(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        line_id_need_change = []
        if vals.get('order_line'):
            for line in vals['order_line']:
                line_id_need_change.append(line[1])
        res = super(PurchaseOrderDefaultGet, self).create(vals)
        line_need_change = self.env['purchase.order.line'].browse(line_id_need_change)
        for line in line_need_change:
            line.order_id = res.id
        return res