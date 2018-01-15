# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockSettings(models.TransientModel):
    _inherit = 'stock.config.settings'

    raw_material_approve_id = fields.Many2one('res.users', string=u'原材料调整审核人')
    finished_material_approve_id = fields.Many2one('res.users', string=u'制成品调整审核人')

    @api.multi
    def set_raw_material_approve_id_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'raw_material_approve_id', self.raw_material_approve_id.id)

    @api.multi
    def set_finished_material_approve_id_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'finished_material_approve_id', self.finished_material_approve_id.id)
