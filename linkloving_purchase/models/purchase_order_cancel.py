# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class PurchaseOrderCancel(models.TransientModel):
    """
    This wizard will cancel the purchase orders
    """

    _name = "purchase.order.cancel"
    _description = "Confirm the selected purchase orders"

    @api.multi
    def order_cancel(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['purchase.order'].browse(active_ids):
            if record.state != 'draft':
                raise UserError(_("只能取消草稿状态的采购单"))
            record.button_cancel()
        return {'type': 'ir.actions.act_window_close'}
