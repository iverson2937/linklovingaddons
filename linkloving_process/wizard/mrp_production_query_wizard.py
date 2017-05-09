# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _


class MrpProductionWizard(models.TransientModel):
    _name = 'mrp.production.query.wizard'

    start_date = fields.Date('Start Date',
                             default=datetime.datetime.now())
    end_date = fields.Date('End Date', default=datetime.datetime.now())

    @api.model
    def _get_process_id(self):
        return self.env['mrp.process'].browse(self._context.get('active_ids'))[0]

    process_id = fields.Many2many('mrp.process', default=_get_process_id)

    @api.multi
    def mo_query(self):
        start_date = datetime.datetime.strptime(self.start_date, "%Y-%m-%d").strftime('%Y-%m-%d %H:%M:%S')
        end_date = (datetime.datetime.strptime(self.end_date, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime(
            '%Y-%m-%d %H:%M:%S')
        if not self.process_id:
            self.process_id = self.env['mrp.process'].search([])
        domain = [('date_planned_start', '>', start_date),
                  ('date_planned_start', '<', end_date), ('process_id', 'in', self.process_id.ids),
                  ('state', 'not in', ['cancel', 'draft'])]
        print domain
        return {
            'name': _('Manufacturing Order'),
            'res_model': 'mrp.production',
            'domain': domain,
            'view_mode': 'tree,form',
            'model': "form",
            'type': 'ir.actions.act_window',
            'target': 'current'
        }
