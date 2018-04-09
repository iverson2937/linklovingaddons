# -*- coding: utf-8 -*-
import json
import logging

import requests
from requests import ConnectionError

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    is_automatic_combine_po = fields.Boolean(string=u'自动合并采购单', default=True)


class ProcurementOrderExtend(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_po(self):
        res = []
        logging.warning("0309_make_po_origin____________")
        for procurement in self:
            suppliers = procurement.product_id.seller_ids.filtered(
                    lambda r: not r.product_id or r.product_id == procurement.product_id)
            if suppliers:
                supplier = suppliers[0]
                partner = supplier.name
                if not partner.is_automatic_combine_po:
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
                    if po:
                        res += [procurement.id]
                    vals = procurement._prepare_purchase_order_line(po, supplier)
                    if vals.get("product_qty") > 0:
                        self.env['purchase.order.line'].create(vals)
                    else:
                        if not po.order_line:
                            po.unlink()
                    return res
                else:
                    return super(ProcurementOrderExtend, procurement).make_po()
            else:
                return super(ProcurementOrderExtend, procurement).make_po()
