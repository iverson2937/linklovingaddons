# -*- coding: utf-8 -*-


from odoo import models, fields, api


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'
    payment_apply_amount = fields.Float(related='company_id.payment_apply_amount')
