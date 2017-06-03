# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmMailMessage(models.Model):
    _inherit = 'mail.message'
    label_ids = fields.Many2many('message.label', string='记录类型')

    postil = fields.Text(string='批注')

    @api.multi
    def send_message_action(self):
        return {'type': 'ir.actions.act_window_close'}
