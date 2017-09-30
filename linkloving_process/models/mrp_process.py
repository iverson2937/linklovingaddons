# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import datetime
import time

from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_is_zero


class MrpProcess(models.Model):
    _name = 'mrp.process'
    _order = 'sequence , name'
    name = fields.Char(string=u'Name')
    description = fields.Text(string=u'Description')
    unit_price = fields.Float(string=u'Price Unit')
    partner_id = fields.Many2one('res.partner', string=u'Responsible By')
    hour_price = fields.Float(string=u'Price Per Hour')
    color = fields.Integer("Color Index")
    count_mo_waiting = fields.Integer(compute='_compute_process_count')
    count_mo_delay = fields.Integer(compute='_compute_process_count')
    count_mo_draft = fields.Integer(compute='_compute_process_count')
    count_mo_today = fields.Integer(compute='_compute_process_count')
    count_mo_tomorrow = fields.Integer(compute='_compute_process_count')
    count_mo_after_tomorrow = fields.Integer(compute='_compute_process_count')
    count_mo_forth_day = fields.Integer(compute='_compute_process_count')
    count_mo_fifth_day = fields.Integer(compute='_compute_process_count')
    count_mo_sixth_day = fields.Integer(compute='_compute_process_count')
    count_mo_others = fields.Integer(compute='_compute_process_count')
    is_outside = fields.Boolean(string=u'是否为委外')
    sequence = fields.Integer()
    total_qty = fields.Integer(compute="_get_total_qty")
    mo_ids = fields.One2many('mrp.production', 'process_id')

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('mrp.process'))

    @api.model
    @api.returns('self', lambda value: value.id)
    def _company_default_get(self, object=False, field=False):
        """ Returns the default company (usually the user's company).
        The 'object' and 'field' arguments are ignored but left here for
        backward compatibility and potential override.
        """
        return self.env['res.users']._get_company()

    @api.multi
    def get_stock_detail(self):
        ids = []
        products = self.env['product.template'].search([('process_id', '=', self.id)])
        for product in products:
            if not float_is_zero(product.qty_available, 2):
                ids.append(product.id)

        return {
            'name': u'库存',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'target': 'current',
            'domain': [('id', 'in', ids)]}

    @api.multi
    def _get_total_qty(self):
        for process in self:
            products = self.env['product.template'].search([('process_id', '=', process.id)])
            process.total_qty = sum(product.qty_available for product in products)

    def _today(self):
        return (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    def _tomorrow(self):
        return (datetime.date.today() + datetime.timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

    def _after_tomorrow(self):
        return (datetime.date.today() + datetime.timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')

    def _forth_day(self):
        return (datetime.date.today() + datetime.timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S')

    def _fifth_day(self):
        return (datetime.date.today() + datetime.timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')

    def _sixth_day(self):
        return (datetime.date.today() + datetime.timedelta(days=6)).strftime('%Y-%m-%d %H:%M:%S')

    @api.multi
    def _compute_process_count(self):
        # TDE TODO count picking can be done using previous two\

        # today_time = fields.datetime.strptime(self.getYesterday(), '%Y-%m-%d')
        # after_day=datetime.timedelta(days=1)

        domains = {
            'count_mo_draft': [('state', '=', 'draft')],
            'count_mo_delay': [('date_planned_start', '<', datetime.date.today().strftime('%Y-%m-%d %H:%M:%S')),
                               ('state', '!=', 'draft')],
            'count_mo_waiting': [('state', 'in', ['draft', 'confirmed', 'waiting_material'])],
            'count_mo_today': [('date_planned_start', '>', datetime.date.today().strftime('%Y-%m-%d %H:%M:%S')),
                               ('state', '!=', 'draft'),
                               ('date_planned_start', '<', self._today())],
            'count_mo_tomorrow': [('date_planned_start', '>', self._today()),
                                  ('state', '!=', 'draft'),
                                  ('date_planned_start', '<', self._tomorrow())],
            'count_mo_after_tomorrow': [('date_planned_start', '>', self._tomorrow()),
                                        ('state', '!=', 'draft'),
                                        ('date_planned_start', '<', self._after_tomorrow())],
            'count_mo_forth_day': [('date_planned_start', '>', self._after_tomorrow()),
                                   ('state', '!=', 'draft'),
                                   ('date_planned_start', '<', self._forth_day())],
            'count_mo_fifth_day': [('date_planned_start', '>', self._forth_day()),
                                   ('state', '!=', 'draft'),
                                   ('date_planned_start', '<', self._fifth_day())],
            'count_mo_sixth_day': [('date_planned_start', '>', self._fifth_day()),
                                   ('date_planned_start', '<', self._sixth_day()), ('state', '!=', 'draft')],
            'count_mo_others': [('date_planned_start', '>', self._after_tomorrow()), ('state', '!=', 'draft')],
        }
        for field in domains:
            data = self.env['mrp.production'].read_group(domains[field] +
                                                         [('state', 'not in', ('done', 'cancel')),
                                                          ('process_id', 'in', self.ids)], ['process_id'],
                                                         ['process_id']
                                                         )
            count = dict(
                map(lambda x: (x['process_id'] and x['process_id'][0], x['process_id_count']), data))
            for record in self:
                record[field] = count.get(record.id, 0)

    @api.multi
    def get_action_mrp_production_tree_to_confirm(self):
        return self._get_action('linkloving_process.action_mrp_production_tree_to_confirm')

    @api.multi
    def get_action_mrp_production_tree_to_combine(self):
        return self._get_action('linkloving_process.get_action_mrp_production_tree_to_combine')

    @api.multi
    def get_action_mrp_production_today(self):
        domain = [('date_planned_start', '>', datetime.date.today().strftime('%Y-%m-%d %H:%M:%S')),
                  ('date_planned_start', '<', self._today()),
                  ('process_id', '=', self.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        return {
            'name': _('Today Mrp Production'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }

    @api.multi
    def get_action_mrp_production_tree_delay(self):
        domain = [('date_planned_start', '<', datetime.date.today().strftime('%Y-%m-%d %H:%M:%S')),
                  ('process_id', '=', self.id), ('state', 'not in', ('done', 'cancel', 'draft'))]
        return {
            'name': _('Delay Mo'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }

    @api.multi
    def get_action_mrp_production_tomorrow(self):
        domain = [('date_planned_start', '>', self._today()), ('date_planned_start', '<', self._tomorrow()),
                  ('process_id', '=', self.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        return {
            'name': _('Tomorrow Mo'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }

    @api.multi
    def get_action_mrp_production_after_tomorrow(self):
        domain = [('date_planned_start', '>', self._tomorrow()), ('date_planned_start', '<', self._after_tomorrow()),
                  ('process_id', '=', self.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        return {
            'name': _('The day after tomorrow MO'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }

    @api.multi
    def get_action_mrp_production_forth_day(self):
        domain = [('date_planned_start', '>', self._after_tomorrow()), ('date_planned_start', '<', self._forth_day()),
                  ('process_id', '=', self.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        return {
            'name': _('The day after tomorrow MO'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }

    @api.multi
    def get_action_mrp_production_fifth_day(self):
        domain = [('date_planned_start', '>', self._forth_day()), ('date_planned_start', '<', self._fifth_day()),
                  ('process_id', '=', self.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        return {
            'name': _('The day after tomorrow MO'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }

    @api.multi
    def get_action_mrp_production_sixth_day(self):
        domain = [('date_planned_start', '>', self._fifth_day()), ('date_planned_start', '<', self._sixth_day()),
                  ('process_id', '=', self.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        return {
            'name': _('The day after tomorrow MO'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }

    @api.multi
    def get_action_mrp_production_others(self):
        domain = [('date_planned_start', '>', self._after_tomorrow()),
                  ('process_id', '=', self.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        return {
            'name': _(''),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }

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

    @api.multi
    def mo_schedule_query(self):
        return {
            'name': _('Query'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production.query.wizard',
            'target': 'new',
        }

    @api.multi
    def unlink(self):
        if any(not process.mo_ids for process in self):
            raise UserError('不可以删除有关联制造单的工序')
        return super(MrpProcess, self).unlink()
