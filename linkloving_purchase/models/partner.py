# -*- coding: utf-8 -*-
import json

from odoo import api
from odoo import models, fields, _


class Partner(models.Model):
    _inherit = 'res.partner'
    supplier_level = fields.Many2one('res.partner.level', string=_('Supplier Level'))
    payment_count = fields.Integer(compute='_compute_payment_count', string='# Payment')
    payment_ids = fields.One2many('account.payment.register', 'partner_id')

    def _compute_payment_count(self):
        for partner in self:
            partner.payment_count = len(partner.payment_ids)

    @api.multi
    def action_view_question_order(self):
        i = 1
        partner_msg = []
        partner_num = 0
        for partner_message in self.message_ids:
            if partner_message.sale_order_type == 'partner_question':
                partner_msg.append({'id': partner_message.id, 'msg_data': partner_message.subject})
                partner_num += 1
        order_question_msg = {0: {'id': self.id, 'so_name': '非订单问题', 'num': partner_num,
                                  'so_partner': partner_msg}}
        for sale_data in self.sale_order_ids:
            # 筛选系统生成的 消息
            sale_msg = []
            sale_num = 0
            for sale_order_msg in sale_data.message_ids:
                if sale_order_msg.sale_order_type == 'question':
                    sale_msg.append({'id': sale_order_msg.id, 'msg_data': sale_order_msg.subject})
                    sale_num += 1
            order_question_msg[i] = {'id': sale_data.id, 'so_name': sale_data.name, 'num': sale_num,
                                     'so_partner': sale_msg}

            # order_question_msg[i] = {'id': sale_data.id, 'so_name': sale_data.name, 'num': len(sale_data.message_ids),
            #                          'so_partner': [{'id': so_order.id,
            #                                          'msg_data': so_order.subject if so_order.subject else so_order.record_name + (
            #                                          u' ' if so_order.sale_order_type == 'inspection' else u' (通知)')} for
            #                                         so_order in sale_data.message_ids]}
            i += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'pantner_order_view',
            'partner_msg_id': order_question_msg
        }
