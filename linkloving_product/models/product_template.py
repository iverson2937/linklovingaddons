# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductTemplate11(models.Model):
    _inherit = 'product.template'
    sub_spec_id = fields.Many2one('product.spec', string=u'子类别')
    spec_id = fields.Many2one('product.spec', string=u'型号')
    partner_id = fields.Many2one('res.partner', domain=[('customer', '=', True), ('is_company', '=', True)],
                                 string=u'客户')

    @api.onchange('categ_id', 'sub_spec_id', 'spec_id', 'partner_id')
    def _get_default_code(self):
        if self.categ_id.code:
            categ_code = self.categ_id.code
            sub_spec_id = self.sub_spec_id.code if self.sub_spec_id else '0'
            spec_id = self.spec_id.code if self.spec_id else '000'
            full_specs = str(sub_spec_id) + str(spec_id)

            if self.partner_id:
                version1 = self.partner_id.customer_code
                if not version1:
                    raise UserError('请设置该客户编码')
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
                        final_version = chr(ord(max(versions)) + 1)
                full_code = '.'.join([categ_code, full_specs, version1, final_version])
                self.default_code = full_code

            else:
                prefix = '.'.join([categ_code, full_specs])
                products = self.env['product.template'].search([('default_code', 'ilike', prefix)])
                if not products:
                    version1 = '000'
                else:
                    versions = []
                    for product in products:
                        if len(product.default_code.split('.')) == 3:
                            versions.append(product.default_code.split('.')[-1])
                    if versions:
                        version1 = '00' + str(int(max(versions)) + 1)
                    else:
                        version1 = '000'
                full_code = '.'.join([categ_code, full_specs, version1])
                self.default_code = full_code

    default_code = fields.Char(track_visibility='onchange')
