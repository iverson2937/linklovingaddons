# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductStateConfirmWizard(models.TransientModel):
    _name = 'product.state.confirm.wizard'
    remark = fields.Char(string='备注')
    reject = fields.Boolean()
    approve = fields.Boolean()
    submit = fields.Boolean()

    @api.multi
    def confirm_submit(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        product_template = self.env['product.template'].browse(active_ids)
        product_template.submit()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def confirm_reject(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        product_template = self.env['product.template'].browse(active_ids)
        product_template.reject(self.remark)
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def confirm_approve(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        product_template = self.env['product.template'].browse(active_ids)
        product_template.approve(self.remark)
        return {'type': 'ir.actions.act_window_close'}
