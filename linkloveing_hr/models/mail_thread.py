# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from collections import namedtuple

from odoo import _, api, exceptions, fields, models, tools

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.multi
    def message_subscribe_users(self, user_ids=None, subtype_ids=None):
        """ 添加sudo() 权限问题 """
        if user_ids is None:
            user_ids = [self._uid]
        return self.message_subscribe(self.env['res.users'].sudo().browse(user_ids).mapped('partner_id').ids,
                                      subtype_ids=subtype_ids)

    @api.multi
    def _get_message_unread(self):
        if not self.ids:
            return
        res = dict((res_id, 0) for res_id in self.ids)
        partner_id = self.env.user.partner_id.id

        # search for unread messages, directly in SQL to improve performances
        self._cr.execute(""" SELECT msg.res_id FROM mail_message msg
                             RIGHT JOIN mail_message_mail_channel_rel rel
                             ON rel.mail_message_id = msg.id
                             RIGHT JOIN mail_channel_partner cp
                             ON (cp.channel_id = rel.mail_channel_id AND cp.partner_id = %s AND
                                (cp.seen_message_id IS NULL OR cp.seen_message_id < msg.id))
                             WHERE msg.model = %s AND msg.res_id in %s AND
                                   (msg.author_id IS NULL OR msg.author_id != %s) AND
                                   (msg.message_type != 'notification' OR msg.model != 'mail.channel')""",
                         (partner_id, self._name, tuple(self.ids), partner_id,))
        for result in self._cr.fetchall():
            res[result[0]] += 1

        for record in self:
            record.message_unread_counter = res.get(record.id, 0)
            record.message_unread = bool(record.message_unread_counter)
