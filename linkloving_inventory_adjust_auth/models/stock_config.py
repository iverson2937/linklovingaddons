# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockSettings(models.TransientModel):
    _inherit = 'stock.config.settings'

    raw_material_approve_id = fields.Many2one('res.users', string=u'原材料调整审核人')
    finished_material_approve_id = fields.Many2one('res.users', string=u'制成品调整审核人')
    wood_material_approve_id = fields.Many2one('res.users', string=u'木板半成品调整审核人')
    stock_adjust_account_id = fields.Many2one('account.account')

    @api.multi
    def set_raw_material_approve_id_defaults(self):
        group = self.env.ref('linkloving_inventory_adjust_auth.group_inventory_user')
        self.raw_material_approve_id.groups_id = [(4, group.id)]
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'raw_material_approve_id', self.raw_material_approve_id.id)

    @api.multi
    def set_wood_material_approve_id_defaults(self):
        group = self.env.ref('linkloving_inventory_adjust_auth.group_inventory_user')
        if self.wood_material_approve_id:
            self.wood_material_approve_id.groups_id = [(4, group.id)]
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'wood_material_approve_id', self.wood_material_approve_id.id)

    @api.multi
    def set_finished_material_approve_id_defaults(self):
        group = self.env.ref('linkloving_inventory_adjust_auth.group_inventory_user')
        self.finished_material_approve_id.groups_id = [(4, group.id)]
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'finished_material_approve_id', self.finished_material_approve_id.id)

    @api.multi
    def set_stock_adjust_account_id_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'stock_adjust_account_id', self.stock_adjust_account_id.id)
