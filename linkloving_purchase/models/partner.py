# -*- coding: utf-8 -*-
from odoo import models, fields, _


class Partner(models.Model):
    _inherit = 'res.partner'
    supplier_level = fields.Many2one('res.partner.level', string=_('Supplier Level'))
    # company_type = fields.Selection(string='Company Type',
    #                             selection=[('company', 'Company'), ('person', 'Individual')],
    #                             compute='_compute_company_type', readonly=False, )
    is_company = fields.Boolean(string='Is a Company', default=True,
                                help="Check if the contact is a company, otherwise it is a person")
    payment_count = fields.Integer(compute='_compute_payment_count', string='# Payment')
    payment_ids = fields.One2many('account.payment.register', 'partner_id')

    def _compute_payment_count(self):
        for partner in self:
            partner.payment_count = len(partner.payment_ids)


class Company(models.Model):
    _inherit = 'res.company'
    official_seal = fields.Binary(string=u'公司公章')
