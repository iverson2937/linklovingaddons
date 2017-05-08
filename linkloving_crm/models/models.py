# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = "crm.lead"
    source = fields.Char(string=u'来源')

    continent = fields.Many2one('crm.continent', string=u'所属大洲')
    # continent = fields.Selection([
    #     ('draft', '亚洲'),
    #     ('draft1', '非洲'),
    #     ('draft2', '北美洲'),
    #     ('draft3', '南美洲'),
    #     ('draft3', '南极洲'),
    #     ('draft3', '欧洲'),
    #     ('draft3', '大洋洲'),
    # ], string=u'所属大洲')
    communication_identifier = fields.Char(string=u'即时通讯号')
    express_sample_record = fields.Char(string=u'快递账号以及寄样记录')
    communicate_in_time = fields.Char(string=u'及时沟通内容')
    follow_up_the_history = fields.Char(string=u'跟进历史记录')
    interested_in_product = fields.Char(string=u'感兴趣产品')


class CrmContinent(models.Model):
    _name = 'crm.continent'

    name = fields.Char(string=u'大洲')
