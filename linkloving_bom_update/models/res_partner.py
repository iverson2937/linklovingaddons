# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    customer_code = fields.Char(string=u'客户简码')
    customer_alias = fields.Char(string=u'客户简称')

    _sql_constraints = [
        ('customer_code', 'unique (customer_code)', u'客户简码不能重复.'),
        ('customer_alias', 'unique (customer_code)', u'客户简称不能重复.'),
    ]
