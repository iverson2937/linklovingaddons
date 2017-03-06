# -*- coding: utf-8 -*-
from odoo import models, fields, _


class Partner(models.Model):
    _inherit = 'res.partner'
    supplier_level = fields.Many2one('res.partner.level', string=_('Supplier Level'))
    payment_count = fields.Integer(compute='_compute_payment_count', string='# Payment')
    payment_ids = fields.One2many('account.payment.register', 'partner_id')

    def _compute_payment_count(self):
        for partner in self:
            partner.payment_count = len(partner.payment_ids)



