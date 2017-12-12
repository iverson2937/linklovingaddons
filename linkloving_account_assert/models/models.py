# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    employee_id = fields.Many2one('hr.employee', string=u'保管人')
    asset_no = fields.Char(string=u'资产编号')
    remark = fields.Char(string=u'备注')
    owner = fields.Selection([
        (1, '江苏若态'),
        (2, '苏州若态'),
        (3, '若贝尔'),
        (4, '鲁班DIY'),
        (5, '板厂'),
    ])