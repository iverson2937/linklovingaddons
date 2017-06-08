# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmMailMessage(models.Model):
    _inherit = 'mail.message'

    messages_label_ids = fields.Many2many('message.label', 'message_label_mail_message_rel', string='记录类型')
    messages_label_body = fields.Char()

    postil = fields.Text(string='批注')

    @api.multi
    def send_message_action(self):
        data = ' '
        for ss in self.messages_label_ids:
            data += (' ' + ss.name)
        self.write({'messages_label_body': data})
        return {'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'view_mode': 'form,tree',
                'view_type': 'form',
                'res_id': self.res_id,
                'target': 'self'}


class CrmMessageLabelStatus(models.Model):
    _name = 'message.order.status'
    name = fields.Char(string=u'订单状态')
    description = fields.Text(string=u'描述')
