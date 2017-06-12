# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReviewProcessWizard(models.TransientModel):
    _inherit = 'review.process.wizard'

    bom_id = fields.Many2one("mrp.bom")
