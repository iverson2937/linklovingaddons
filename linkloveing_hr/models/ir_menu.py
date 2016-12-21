# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import operator
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.modules import get_module_resource
from odoo.tools.safe_eval import safe_eval


class ir_ui_menu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.multi
    def get_needaction_data(self):
        """ Return for each menu entry in ``self``:
            - whether it uses the needaction mechanism (needaction_enabled)
            - the needaction counter of the related action, taking into account
              the action domain
        """
        menu_ids = set()
        for menu in self:
            menu_ids.add(menu.id)
            ctx = {}
            if menu.action and menu.action.type in (
                    'ir.actions.act_window', 'ir.actions.client') and menu.action.context:
                with tools.ignore(Exception):
                    # use magical UnquoteEvalContext to ignore undefined client-side variables such as `active_id`
                    eval_ctx = tools.UnquoteEvalContext(self._context)
                    ctx = safe_eval(menu.action.context, locals_dict=eval_ctx, nocopy=True) or {}
            menu_refs = ctx.get('needaction_menu_ref')
            if menu_refs:
                if not isinstance(menu_refs, list):
                    menu_refs = [menu_refs]
                for menu_ref in menu_refs:
                    record = self.env.ref(menu_ref, False)
                    if record and record._name == 'ir.ui.menu':
                        menu_ids.add(record.id)

        res = {}
        for menu in self.browse(menu_ids):
            res[menu.id] = {
                'needaction_enabled': False,
                'needaction_counter': False,
            }
            if menu.action and menu.action.type in (
                    'ir.actions.act_window', 'ir.actions.client') and menu.action.res_model:
                if menu.action.res_model in self.env:
                    model = self.env[menu.action.res_model]
                    if menu.action.context != u'{}':
                        try:
                            model = self.env[menu.action.res_model].with_context(**eval(menu.action.context.strip()))
                        except Exception:
                            pass

                    if model._needaction:
                        if menu.action.type == 'ir.actions.act_window':
                            eval_context = self.env['ir.actions.act_window']._get_eval_context()
                            dom = safe_eval(menu.action.domain or '[]', eval_context)
                        else:
                            dom = safe_eval(menu.action.params_store or '{}', {'uid': self._uid}).get('domain')
                        res[menu.id]['needaction_enabled'] = model._needaction
                        res[menu.id]['needaction_counter'] = model._needaction_count(dom)
        return res
