# -*- coding: utf-8 -*-

from odoo import models, fields, api


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
        pre_fix = '.'.join([self.cate])
        customer_code = self.partner_id.customer_code if self.partner_id else version
