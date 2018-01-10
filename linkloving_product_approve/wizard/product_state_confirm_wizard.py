# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.TransientModel):
    _name = 'product.state.confirm.wizard'
    remark = fields.Char(string='备注')

    @api.multi
    def confirm_submit(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        product_template = self.env['product.template'].browse(active_ids)
        product_template.submit()
        return {'type': 'ir.actions.act_window_close'}
