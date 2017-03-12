# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import datetime
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpProcess(models.Model):
    _name = 'mrp.process'
    name = fields.Char(string=u'Name')
    description = fields.Text(string=u'Description')
    unit_price = fields.Float(string=u'Price Unit')
    partner_id = fields.Many2one('res.partner', string=u'Responsible By',
                                 domain="[('is_in_charge','=',True)]")
    hour_price = fields.Float(string=u'Price Per Hour')
    color = fields.Integer("Color Index")
    count_process_ready=fields.Integer()
    count_process_draft = fields.Integer(compute='_compute_process_count')
    count_process_today = fields.Integer(compute='_compute_process_count')
    count_process_tomorrow = fields.Integer(compute='_compute_process_count')
    count_process_after_tomorrow = fields.Integer(compute='_compute_process_count')
    count_process_other = fields.Integer(compute='_compute_process_count')
    def getYesterday(self):  #
        today = datetime.date.today()
        oneday = datetime.timedelta(days=1)
        yesterday = today + oneday
        return str(yesterday)

    @api.multi
    def _compute_process_count(self):
        # TDE TODO count picking can be done using previous two\

        today_time = fields.datetime.strptime(self.getYesterday(), '%Y-%m-%d')
        after_day=datetime.timedelta(days=1)

        domains = {
            'count_process_draft': [('state', '=', 'draft')],
            'count_process_today': [('date_planned_start', '>', today_time.strftime('%Y-%m-%d %H:%M:%S')),('date_planned_start', '<', after_day.strftime('%Y-%m-%d %H:%M:%S'))],
            'count_process_tomorrow': 1,
            'count_process_after_tomorrow': 1,
            'count_process_other': 1,

        }
        for field in domains:
            data = self.env['mrp.production'].read_group(domains[field] +
                                                        [('state', 'not in', ('done', 'cancel')),
                                                         ('picking_type_id', 'in', self.ids)],
                                                 )
            count = dict(
                map(lambda x: (x['picking_type_id'] and x['picking_type_id'][0], x['picking_type_id_count']), data))
            for record in self:
                record[field] = count.get(record.id, 0)

        # datetime.datetime.today() + datetime.timedelta(days=2)
        self.count_process_ready = 1
        self.count_process_ready = 1
        self.count_process_tomorrow = 1
        self.count_process_other = 1

    @api.multi
    def get_action_mrp_production_tree_to_confirm(self):
        return self._get_action('linkloving_process.action_mrp_production_tree_to_confirm')

    @api.multi
    def _get_action(self, action_xmlid):
        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
        return action

        # domains = {
        #     'count_picking_draft': [('state', '=', 'draft')],
        #     'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
        #     'count_picking_ready': [('state', 'in', ('assigned', 'partially_available'))],
        #     'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available'))],
        #     'count_picking_late': [('min_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed', 'partially_available'))],
        #     'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting', 'partially_available'))],
        # }
        # for field in domains:
        #     data = self.env['stock.picking'].read_group(domains[field] +
        #         [('state', 'not in', ('done', 'cancel')), ('picking_type_id', 'in', self.ids)],
        #         ['picking_type_id'], ['picking_type_id'])
        #     count = dict(map(lambda x: (x['picking_type_id'] and x['picking_type_id'][0], x['picking_type_id_count']), data))
        #     for record in self:
        #         record[field] = count.get(record.id, 0)
        # for record in self:
        #     record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
        #     record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0
