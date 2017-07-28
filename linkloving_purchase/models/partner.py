# -*- coding: utf-8 -*-
import json

from odoo import api
from odoo import models, fields, _


class Partner(models.Model):
    _inherit = 'res.partner'
    supplier_level = fields.Many2one('res.partner.level', string=_('Supplier Level'))
    payment_count = fields.Integer(compute='_compute_payment_count', string='# Payment')
    payment_ids = fields.One2many('account.payment.register', 'partner_id')

    order_partner_question_count = fields.Integer(compute='_compute_order_partner_question', string=u'客户问题汇总')

    def _compute_payment_count(self):
        for partner in self:
            partner.payment_count = len(partner.payment_ids)

    def _compute_order_partner_question(self):
        for partner in self:
            count = 0
            for sale_order in partner.sale_order_ids:
                count += len(sale_order.message_ids)
            partner.order_partner_question_count = len(partner.message_ids) + count

    @api.multi
    def action_view_question_order(self):

        # action = self.env.ref('linkloving_sale.sale_action_partner_form').read()[0]
        # data = dict
        # ((order_data.name, [data_adc for data_adc in order_data.message_ids]) for order_data in
        #  self.sale_order_ids)
        # print data

        i = 1
        order_question_msg = {0: {'id': self.id, 'so_name': '非订单问题', 'num': len(self.message_ids),
                                  'so_partner': [{'id': self_data.id, 'msg_data': self_data.compyter_body} for self_data
                                                 in self.message_ids]}}

        for sale_data in self.sale_order_ids:
            # 筛选系统生成的 消息
            # adc = []
            # for sale_order_msg in sale_data.message_ids:
            #     if sale_order_msg.message_type != 'notification':
            #         adc.append({'id': sale_order_msg.id, 'msg_data': sale_order_msg.subject})
            #
            # order_question_msg[i] = {'id': sale_data.id, 'so_name': sale_data.name, 'num': len(sale_data.message_ids),
            #                          'so_partner': adc}

            order_question_msg[i] = {'id': sale_data.id, 'so_name': sale_data.name, 'num': len(sale_data.message_ids),
                                     'so_partner': [{'id': so_order.id,
                                                     'msg_data': so_order.subject if so_order.subject else so_order.record_name + u'(通知)'}
                                                    for so_order in sale_data.message_ids]}
            i += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'pantner_order_view',
            'partner_msg_id': order_question_msg
        }
