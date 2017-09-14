# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from odoo import fields, api, models


class CrmTeam(models.Model):
    _inherit = "crm.team"
    orders_to_ship_count = fields.Integer(compute='_compute_count')
    draft_orders_count = fields.Integer(compute='_compute_count')
    sales_to_invoice_count = fields.Integer(compute="_compute_count")
    is_show = fields.Boolean(string=u'是否显示')
    invoice_amount = fields.Integer(compute='_compute_invoice')

    def _compute_invoice(self):
        domains = {
            'invoice_amount': [('state', 'not in', ('cancel', 'paid'))],
        }
        for field in domains:
            data = self.env['account.invoice'].read_group(domains[field] +
                                                          [
                                                              ('team_id', 'in', self.ids)], ['team_id'],
                                                          ['team_id']
                                                          )
            count = dict(
                map(lambda x: (x['team_id'] and x['team_id'][0], x['team_id_count']), data))
            print count
            for record in self:
                record[field] = count.get(record.id, 0)

    def _compute_count(self):
        domains = {
            'orders_to_ship_count': [('state', '=', 'sale'), ('shipping_status', '!=', 'done')],

            'draft_orders_count': [('state', '=', 'draft')],
            'sales_to_invoice_count': [('state', '=', 'sale'), ('invoice_status', '=', 'to invoice')],
        }
        for field in domains:
            data = self.env['sale.order'].read_group(domains[field] +
                                                     [
                                                         ('team_id', 'in', self.ids)], ['team_id'],
                                                     ['team_id']
                                                     )
            count = dict(
                map(lambda x: (x['team_id'] and x['team_id'][0], x['team_id_count']), data))
            print count
            for record in self:
                record[field] = count.get(record.id, 0)
