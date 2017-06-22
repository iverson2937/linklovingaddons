# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmMessageLabel(models.Model):
    _name = 'message.label'
    name = fields.Char(string=u'名称')
    description = fields.Text(string=u'描述')
    message_type_img = fields.Binary(attachment=True, string=u'照片')

    @api.model
    def get_message_label_name(self):
        msg_label = self.env['message.label'].search([])
        msg_label_data = [{'name': msg.name, 'id': msg.id} for msg in msg_label]
        return msg_label_data
