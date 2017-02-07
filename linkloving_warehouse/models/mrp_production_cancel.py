# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class MrpProductionCancel(models.TransientModel):
    """
    This wizard will cancel the mrp production
    """

    _name = "mrp.production.cancel"
    _description = "Confirm cancel the selected mo"

    @api.multi
    def action_cancel(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['mrp.production'].browse(active_ids):
            if record.state != 'confirmed':
                raise UserError(_("只能取消确定状态的MO"))
            record.action_cancel()
        return {'type': 'ir.actions.act_window_close'}