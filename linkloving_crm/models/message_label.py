# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmMessageLabel(models.Model):
    _name = 'message.label'
    name = fields.Char(string=u'名称')
    description = fields.Text(string=u'描述')
