# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    state = fields.Selection([
        ('draft', u'草稿'),
        ('post', u'提交'),
        ('document', u'文控审核'),
        ('engineer', u'工程审核'),
        ('ｍarket', u'市场'),
        ('done', u'正式')
    ], string=u'状态', default='draft')

    @api.multi
    def action_post(self):
        self.state = 'document'

    @api.multi
    def action_document(self):
        self.state = 'document'
