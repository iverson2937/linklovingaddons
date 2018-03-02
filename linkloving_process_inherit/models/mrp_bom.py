# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBomLine(models.Model):
    _name = 'mrp.bom.line'
    action_id = fields.Many2one('mrp.process.action')
