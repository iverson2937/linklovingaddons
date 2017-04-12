# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class SaleOrderCancel(models.TransientModel):
    """
    This wizard will cancel the mrp production
    """

    _name = "sale.order.cancel"
    _description = "Confirm cancel the sale  order"

    @api.multi
    def action_cancel(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['sale.order'].browse(active_ids):
            if record.invoice_status != 'no':
                raise UserError(u"只可删除待发货状态的销售单")
            record.action_cancel()
        return {'type': 'ir.actions.act_window_close'}
