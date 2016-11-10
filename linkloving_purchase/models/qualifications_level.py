# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class ResPartnerLevel(models.Model):
    """
    供应商资质等级
    """
    _name = 'res.partner.level'
    name = fields.Char(string=_('Qualification Level'))
    level_type = fields.Selection([
        ('1', u'客户等级'),
        ('2', u'厂商等级')
    ])
    description = fields.Text(string=_('Description'))
