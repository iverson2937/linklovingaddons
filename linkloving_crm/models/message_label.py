# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmMessageLabel(models.Model):
    _name = 'message.label'
    name = fields.Char(string=u'名称')
    description = fields.Text(string=u'描述')
    message_type_img_id = fields.One2many('ir.attachment', 'img_messages_label_id', string='图片地址')


class CrmMessageLabelImg(models.Model):
    _inherit = 'ir.attachment'
    img_messages_label_id = fields.Many2one('message.label', string='绑定类型')
