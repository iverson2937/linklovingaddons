# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from odoo import fields, api, models


class CrmTeam(models.Model):
    _inherit = "crm.team"
    code = fields.Char(string=u'Simple code')
    follow_id = fields.Many2one('res.users', string=u'跟单员')
    # for inner_code
    is_domestic = fields.Boolean(string=u'Is Domestic team')

    orders_to_ship_count = fields.Integer(compute='_compute_count')
    draft_orders_count = fields.Integer(compute='_compute_count')
    sales_to_invoice_count = fields.Integer(compute="_compute_count")

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
            for record in self:
                record[field] = count.get(record.id, 0)
