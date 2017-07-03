# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    sub_spec_id = fields.Many2one('product.spec', string=u'子类别')
    spec_id = fields.Many2one('product.spec', string=u'型号')
    partner_id = fields.Many2one('res.partner', domain=[('customer', '=', True), ('is_company', '=', True)],
                                 string=u'客户')
    default_code = fields.Char(compute='get_default_code', store=True)

    def get_default_code(self):
        categ_code = self.categ_id.code
        sub_spec_id = self.sub_spec_id.code if self.sub_spec_id else 0
        spec_id = self.spec_id.code
        full_specs = sub_spec_id + spec_id

        if self.partner_id:
            version1 = self.partner_id.customer_code
            prefix = '.'.join([categ_code, full_specs, version1])
            products = self.env['product.template'].search([('default_code', 'ilike', prefix)])
            if not products:
                final_version = 'A'
            else:
                versions = []
                for product in products:
                    if len(product.default_code.split('.')) > 3:
                        versions.append(product.default_code.split('.')[-1])
                if not versions:
                    final_version = 'B'
                else:
                    final_version = max(versions + 1)
            return '.'.join([categ_code, full_specs, version1, final_version])

        else:
            prefix = '.'.join([categ_code, full_specs])
            products = self.env['product.template'].search([('default_code', 'ilike', prefix)])
            if not products:
                version1 = 000
            else:
                versions = []
                for product in products:
                    versions.append(product.default_code.split('.')[-1])
                version1 = max(versions + 1)
            return '.'.join([categ_code, full_specs, version1])
