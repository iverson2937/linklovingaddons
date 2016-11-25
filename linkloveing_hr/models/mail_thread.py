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
