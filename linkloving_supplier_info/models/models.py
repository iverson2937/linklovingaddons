# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    supplier_product_code = fields.Char(string=u'供应商码', compute='_get_supplier_product_code',
                                        inverse='_set_supplier_product_code')

    @api.multi
    def _get_supplier_product_code(self):
        for line in self:
            seller_ids = line.product_id.product_tmpl_id.seller_ids.filtered(
                lambda x: x.name.id == line.order_id.partner_id.id)
            if seller_ids:
                line.supplier_product_code = seller_ids[0].product_code

    @api.multi
    def _set_supplier_product_code(self):
        for line in self:
            seller_ids = line.product_id.product_tmpl_id.seller_ids.filtered(
                lambda x: x.name.id == line.order_id.partner_id.id)
            if seller_ids:
                for info in seller_ids:
                    info.product_code = line.supplier_product_code
            else:
                self.env['product.supplierinfo'].create({
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'product_code': line.supplier_product_code,
                    'name': line.order_id.partner_id.id
                })

    @api.onchange('product_id')
    def onchange_product_id(self):
        seller_ids = self.product_id.product_tmpl_id.seller_ids.filtered(
            lambda x: x.name.id == self.order_id.partner_id.id)
        if seller_ids:
            self.supplier_product_code = seller_ids[0].product_code

        return super(PurchaseOrderLine, self).onchange_product_id()
