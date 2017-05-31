# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class MailMessage(models.Model):
    _inherit = 'mail.message'
    label_ids = fields.Many2many('message.label', string='记录类型')
