# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = "crm.lead"
    source = fields.Char(string=u'来源')

    continent = fields.Many2one('crm.continent', string=u'所属大洲')
    express_sample_record = fields.Char(string=u'快递账号')
    interested_in_product = fields.Char(string=u'感兴趣产品')

    communication_identifier = fields.Char(string=u'其他沟通方式')
    qq = fields.Char(string=u'QQ')
    wechat = fields.Char(string=u'微信')
    whatsapp = fields.Char(string=u'WhatsApp')
    skype = fields.Char(string=u'Skype')


class CrmContinent(models.Model):
    _name = 'crm.continent'

    name = fields.Char(string=u'大洲')
