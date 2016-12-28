# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    owner = fields.Char(string=u'账户姓名')
    bank_description = fields.Char(string=u'银行名称')

    @api.multi
    @api.depends('acc_number', 'bank_description', 'owner')
    def name_get(self):
        result = []
        for bank in self:
            name = ' '.join(
                [bank.bank_description if bank.bank_description else '', bank.acc_number, bank.owner if bank.owner else ''])
            result.append((bank.id, name))
        return result
