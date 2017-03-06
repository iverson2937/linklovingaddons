# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    owner = fields.Char(string=u'Name')

    @api.multi
    @api.depends('acc_number', 'bank_id', 'owner')
    def name_get(self):
        result = []
        for bank in self:
            name = ' '.join(
                [bank.bank_id.name if bank.bank_id else '', bank.acc_number,
                 bank.owner if bank.owner else ''])
            result.append((bank.id, name))
        return result
