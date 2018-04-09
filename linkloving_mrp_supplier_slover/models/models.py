# -*- coding: utf-8 -*-
from collections import defaultdict
from sqlite3 import OperationalError

from odoo import models, fields, api, _, registry
from odoo.exceptions import UserError
from odoo.osv import osv
from odoo.tools import float_compare, float_round


class PurchaseConfiguration(models.TransientModel):
    _inherit = 'purchase.config.settings'

    combine_rule = fields.Selection(selection=[('same_supplier', u'相同供应商'),
                                               ('same_supplier_product', u'相同供应商和产品'),
                                               ('same_supplier_origin', u'相同供应商和源')],
                                    default='same_supplier',
                                    string=u'采购单合并规则')

    @api.model
    def get_default_combine_rule(self, m_fields):
        dica = {}
        fi_val = self.env["ir.config_parameter"].get_param("purchase.config.settings.combine_rule", default=None)
        dica.update({
            'combine_rule': fi_val
        })

        return dica

    @api.multi
    def set_combine_rule(self):
        m_fields = ['combine_rule']
        for record in self:
            for fi in m_fields:
                self.env['ir.config_parameter'].set_param("purchase.config.settings.%s" % fi,
                                                          getattr(record, fi, 'same_supplier'))

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[('make_by_mrp', u'由MRP生成')])

    # @api.one
    # def write(self, vals):
    #     res = super(PurchaseOrder, self).write(vals)
    #     if 'state' not in vals.keys():
    #         is_exception_order = self.partner_id == self.env.ref(
    #             'linkloving_mrp_supplier_slover.res_partner_exception_supplier')
    #         if is_exception_order:
    #             self.check_product_has_supplier()
    #     return res

    @api.depends('order_line.date_planned')
    def _compute_date_planned(self):
        for order in self:
            min_date = False
            if not order.order_line:
                order.date_planned = fields.Datetime.now()
            for line in order.order_line:
                if not min_date or line.date_planned < min_date:
                    min_date = line.date_planned
            if min_date:
                order.date_planned = min_date

    @api.multi
    def button_confirm(self):
        is_exception_order = self.partner_id == self.env.ref('linkloving_mrp_supplier_slover.res_partner_exception_supplier')
        if is_exception_order:
            raise UserError(_("此为未设置供应商的产品列表，不可做此操作，请将下列产品设置供应商后，点击'检查供应商'按钮！"))
            return
        return super(PurchaseOrder, self).button_confirm()

    def is_exception_order(self):
        is_exception_order = self.partner_id == self.env.ref('linkloving_mrp_supplier_slover.res_partner_exception_supplier')
        return is_exception_order
    @api.one
    def check_product_has_supplier(self):
        is_exception_order = self.partner_id == self.env.ref('linkloving_mrp_supplier_slover.res_partner_exception_supplier')
        if not is_exception_order:
            raise UserError(_("此单据供应商不可做此操作！"))
            return
        for r in self.order_line:
            if r.product_id.seller_ids:
                id_to_delete = r.id
                proc_obj = self.env['procurement.order'].search([('purchase_line_id', '=', id_to_delete)])
                r.unlink()
                if proc_obj:
                    proc_obj.run()
                    # if not self.order_line:
                    #     self.state = 'cancel'
                    #     self.unlink()

class linkloving_procurement_order(models.Model):
    _inherit = 'procurement.order'

    # unlink_remark = fields.Char(string='删除原因')
    @api.multi
    def make_po(self):
        cache = {}
        res = []
        combine_rule = self.env['purchase.config.settings'].get_default_combine_rule([]).get("combine_rule")
        for procurement in self:
            product_new_qty = procurement.product_qty if self.not_base_on_available else procurement.get_actual_require_qty()
            procurement_uom_po_qty = procurement.product_uom._compute_quantity(product_new_qty, procurement.product_id.uom_po_id)
            if procurement_uom_po_qty <= 0:
                res += [procurement.id]
                continue
            suppliers = procurement.product_id.seller_ids.filtered(
                lambda r: not r.product_id or r.product_id == procurement.product_id)
            supplier = None
            if not suppliers:
                supplier = self.sudo().env.ref(
                    'linkloving_mrp_supplier_slover.supplierinfo_eeeee')
                procurement.message_post(
                    body=_('No vendor associated to product %s. Please set one to fix this procurement.') % (
                    procurement.product_id.name))
            if not supplier:
                supplier = suppliers[0]
            partner = supplier.name

            # gpo = procurement.rule_id.group_propagation_option
            # group = (gpo == 'fixed' and procurement.rule_id.group_id) or \
            #         (gpo == 'propagate' and procurement.group_id) or False
            domain = (
                ('partner_id', '=', partner.id),
                ('state', '=', 'make_by_mrp'),
                # ('picking_type_id', '=', procurement.rule_id.picking_type_id.id),
                ('company_id', '=', procurement.company_id.id),
                # ('dest_address_id', '=', procurement.partner_dest_id.id)
            )
            if combine_rule == 'same_supplier_origin':
                domain += (('origin', '=', self.origin),)
            # if group:
            #     domain += (('group_id', '=', group.id),)

            if domain in cache:
                po = cache[domain]
            else:  # 相同供应商合并
                po = self.env['purchase.order'].search([dom for dom in domain])
                po = po[0] if po else False
                cache[domain] = po
                # 不合并
                # po = None
                # pos = self.env['purchase.order'].search([dom for dom in domain])
                # for po1 in pos:
                #     for line in po1.order_line:
                #         if line.product_id.id == self.product_id.id:
                #             po = po1  #
                #             break
                # if po:
                #     cache[domain] = po

            if not po:  # 如果找不到对应的po
                if combine_rule != 'same_supplier_product':
                    vals = procurement._prepare_purchase_order(partner)
                    # tax_id = self.env["account.tax"].search([('type_tax_use', '<>', "purchase")], limit=1)[0].id
                    # vals["tax"]
                    vals['state'] = "make_by_mrp"
                    po = self.env['purchase.order'].create(vals)
                    name = (procurement.group_id and (procurement.group_id.name + ":") or "") + (
                        procurement.name != "/" and procurement.name or procurement.move_dest_id.raw_material_production_id and procurement.move_dest_id.raw_material_production_id.name or "")
                    message = _(
                            "This purchase order has been created from: <a href=# data-oe-model=procurement.order data-oe-id=%d>%s</a>") % (
                                  procurement.id, name)
                    po.message_post(body=message)
                    cache[domain] = po
                else:
                    po = self.env['purchase.order']
            elif not po.origin or procurement.origin not in po.origin.split(', '):
                # Keep track of all procurements
                if po.origin:
                    if procurement.origin:
                        po.write({'origin': po.origin + ', ' + procurement.origin})
                    else:
                        po.write({'origin': po.origin})
                else:
                    po.write({'origin': procurement.origin})
                name = (self.group_id and (self.group_id.name + ":") or "") + (
                self.name != "/" and self.name or self.move_dest_id.raw_material_production_id and self.move_dest_id.raw_material_production_id.name or "")
                message = _(
                    "This purchase order has been modified from: <a href=# data-oe-model=procurement.order data-oe-id=%d>%s</a>") % (
                          procurement.id, name)
                po.message_post(body=message)
            if po:
                res += [procurement.id]

            # Create Line
            po_line = False
            for line in po.order_line:
                if line.product_id == procurement.product_id and line.product_uom == procurement.product_id.uom_po_id:
                    procurement_uom_po_qty = procurement.product_uom._compute_quantity(product_new_qty,
                                                                                       procurement.product_id.uom_po_id)
                    seller = procurement.product_id._select_seller(
                            partner_id=partner,
                            quantity=line.product_qty + procurement_uom_po_qty,
                            date=po.date_order and po.date_order[:10],
                            uom_id=procurement.product_id.uom_po_id)

                    price_unit = self.env['account.tax']._fix_tax_included_price(seller.price,
                                                                                 line.product_id.supplier_taxes_id,
                                                                                 line.taxes_id) if seller else 0.0
                    if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
                        price_unit = seller.currency_id.compute(price_unit, po.currency_id)

                    po_line = line.write({
                        'product_qty': line.product_qty + procurement_uom_po_qty,
                        'price_unit': price_unit,
                        'procurement_ids': [(4, procurement.id)]
                    })
                    break
            if not po_line:
                new_po = po
                if combine_rule == 'same_supplier_product':
                    po_vals = procurement._prepare_purchase_order(partner)
                    # tax_id = self.env["account.tax"].search([('type_tax_use', '<>', "purchase")], limit=1)[0].id
                    # vals["tax"]
                    po_vals['state'] = "make_by_mrp"
                    new_po = self.env['purchase.order'].create(po_vals)
                    name = (procurement.group_id and (procurement.group_id.name + ":") or "") + (
                        procurement.name != "/" and procurement.name or procurement.move_dest_id.raw_material_production_id and procurement.move_dest_id.raw_material_production_id.name or "")
                    message = _(
                            "This purchase order has been created from: <a href=# data-oe-model=procurement.order data-oe-id=%d>%s</a>") % (
                                  procurement.id, name)
                    po.message_post(body=message)
                    cache[domain] = new_po

                vals = procurement._prepare_purchase_order_line(new_po, supplier)
                if vals.get("product_qty") > 0:
                    self.env['purchase.order.line'].create(vals)
        return res


class LinklovingPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def unlink(self):
        is_exception_order = self.order_id.partner_id == self.sudo().env.ref('linkloving_mrp_supplier_slover.res_partner_exception_supplier')
        if True:
            order = self.order_id
            res = super(LinklovingPurchaseOrderLine, self).unlink()
            if not order.order_line:
                order.unlink()
            return res
        else:
            if self.product_id.seller_ids:
                id_to_delete = self.id
                proc_obj = self.env['procurement.order'].search([('purchase_line_id', '=', id_to_delete)])
                super(LinklovingPurchaseOrderLine, self).unlink()
                if proc_obj:
                    proc_obj.run()
                # if not self.order_id.order_line:
                #     self.order_id.unlink()
            else:
                raise UserError(_('产品还未设置供应商，不可从订单中删除'))
