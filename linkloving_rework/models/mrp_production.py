# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    is_rework = fields.Boolean(related='process_id.is_rework', store=True)
    rework_material_line_ids = fields.One2many('rework.material.line', 'mo_id')

    @api.onchange('process_id')
    def onchange_process_id(self):
        if self.process_id.is_rework:
            pass
