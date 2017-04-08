# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    state = fields.Selection([
        ('draft', u'草稿'),
        ('post', u'提交'),
        ('done', u'正式')
    ], string=u'状态', default='draft')
