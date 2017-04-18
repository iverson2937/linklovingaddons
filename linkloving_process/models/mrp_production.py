# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    process_id = fields.Many2one('mrp.process', string=u'Process')
    is_outside = fields.Boolean(related='process_id.is_outside', store=True)
    supplier_id = fields.Many2one('res.partner', domain=[('supplier', '=', True)], string=u'加工商')
    tracking_number = fields.Char(string=u'物流单号')
    unit_price = fields.Float()

    @api.multi
    def _prepare_invoice(self):
        inv_obj = self.env['account.invoice']

        account_id = self.supplier_id.property_account_payable_id.id
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.supplier_id.name,))

        invoice = inv_obj.create({
            'origin': self.name,
            'type': 'in_invoice',
            'reference': False,
            'account_id': account_id,
            'partner_id': self.supplier_id.id,
            # 'partner_shipping_id': order.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'origin': self.name,
                'price_unit': self.unit_price,
                'account_id': 47,
                'quantity': self.qty_produced,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                # 'invoice_line_tax_ids': [(4, order.tax_id.id)],
                # 'account_analytic_id': order.project_id.id or False,
            })],
            # 'currency_id': order.pricelist_id.currency_id.id,
            # 'team_id': order.team_id.id,
            # 'comment': order.note,
        })
        # invoice.compute_taxes()
        # invoice.message_post_with_view('mail.message_origin_link',
        #             values={'self': invoice, 'origin': order},
        #             subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    @api.one
    def get_mo_count(self):
        date_planned_start = datetime.datetime.strptime(self.date_planned_start, "%Y-%m-%d %H:%M:%S").strftime(
            '%Y-%m-%d')
        start = date_planned_start + ' 00:00:00'
        end = date_planned_start + ' 23:59:59'

        domain = [('date_planned_start', '>', start),
                  ('date_planned_start', '<', end),
                  ('process_id', '=', self.process_id.id), ('state', 'not in', ('done', 'cancel', 'draft'))]

        self.mo_count = len(self.env['mrp.production'].search(domain).ids)

    @api.one
    def get_mo_inovice(self):

        self.mo_invoice_count = len(self.env['account.invoice'].search([('origin', '=', self.name)]).ids)

    mo_count = fields.Integer(compute=get_mo_count)

    mo_invoice_count = fields.Integer(compute=get_mo_inovice)
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
        self.unit_price = self.bom_id.unit_price
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

    @api.multi
    def action_view_mrp_invoice(self):
        print self.env['account.invoice'].search([('origin', '=', self.name)]).ids


        return {
            'name': _('对账单'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'target': 'current',
            'res_id': self.env['account.invoice'].search([('origin', '=', self.name)]).ids[0],
        }

    @api.multi
    def button_mark_done(self):
        print 'is_outside', self.is_outside
        if self.is_outside:
            self._prepare_invoice()
        return super(MrpProduction, self).button_mark_done()
