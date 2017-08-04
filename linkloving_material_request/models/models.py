# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MaterialRequest(models.Model):
    _name = 'material.request'

    name = fields.Char()
    date_order = fields.Date(string=u'单据日期')
    request_date = fields.Date(string=u'交货日期')
    request_type = fields.Selection([
        ('material_request', u'领料'),
        ('make_sample', u'打样')
    ], default='material_request',help="The 'Internal Type' is used for features available on "\
        "different types of accounts: liquidity type is for cash or bank accounts"\
        ", payable/receivable is for vendor/customer accounts.")
    remark = fields.Char(string=u'领料原因')
    send_material_way=fields.Selection([
        ('logistics',u'物流发料'),
        ('line', u'产线领料'),
        ('')
    ])
