# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    process_id = fields.Many2one('mrp.process', string=u'Process')
    unit_price = fields.Float()

    @api.one
    def get_mo_count(self):
        date_planned_start = datetime.datetime.strptime(self.date_planned_start, "%Y-%m-%d %H:%M:%S").strftime(
            '%Y-%m-%d')
        start = date_planned_start + ' 00:00:00'
        end = date_planned_start + ' 23:59:59'

        domain = [('date_planned_start', '>', start),
                  ('date_planned_start', '<', end),
                  ('process_id', '=', self.process_id.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        self.mo_count= len(self.env['mrp.production'].search(domain).ids)

    mo_count = fields.Integer(compute=get_mo_count)
    mo_type = fields.Selection([
        ('unit', _('Base on Unit')),
        ('time', _('Base on Time')),
    ], default='unit')
    hour_price = fields.Float(string=u'Price Per Hour')
    in_charge_id = fields.Many2one('res.partner')
    product_qty = fields.Float(
        _('Quantity To Produce'),
        default=1.0, digits=dp.get_precision('Payroll'),
        readonly=True, required=True,
        states={'confirmed': [('readonly', False)]})

    @api.onchange('bom_id')
    def on_change_bom_id(self):
        self.process_id = self.bom_id.process_id
        self.unit_price = self.process_id.unit_price
        self.mo_type = self.bom_id.mo_type
        self.hour_price = self.bom_id.hour_price
        self.in_charge_id = self.process_id.partner_id

    @api.multi
    def action_view_mrp_productions(self):
        date_planned_start = datetime.datetime.strptime(self.date_planned_start, "%Y-%m-%d %H:%M:%S").strftime(
            '%Y-%m-%d')
        start = date_planned_start + ' 00:00:00'
        end = date_planned_start + ' 23:59:59'

        domain = [('date_planned_start', '>', start),
                  ('date_planned_start', '<', end),
                  ('process_id', '=', self.process_id.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        return {
            'name': _('Current Day Mrp Production'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'target': 'current',
            'domain': domain,
        }
