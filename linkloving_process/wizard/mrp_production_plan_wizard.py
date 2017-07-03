# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpProductionWizard(models.TransientModel):
    _name = 'mrp.production.plan.wizard'

    date_planned_start = fields.Datetime(
        u'开始时间', default=fields.Datetime.now)
    date_planned_finished = fields.Datetime(
        u'结束时间', default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='工序负责人')
    is_set_start = fields.Boolean(default=True)

    @api.multi
    def action_mo_plan(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['mrp.production'].browse(active_ids):
            if record.state not in ['draft', 'confirmed', 'waiting_material']:
                raise UserError((u"%s 已经 %s ,不能重新安排生产日期") % (record.name, record.state))
            record.date_planned_start = self.date_planned_start
            record.date_planned_finished = self.date_planned_finished
            if self.partner_id:
                record.in_charge_id = self.partner_id
            if self.is_set_start:
                record.state = 'waiting_material'
