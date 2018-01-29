# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    secondary_operation = fields.Boolean(string=u'是否二次加工', track_visibility='onchange')


class StockPickingExtend(models.Model):
    _inherit = 'stock.picking'

    secondary_operation = fields.Boolean(string=u'是否二次加工', related='sale_id.secondary_operation')
    timesheet_order_ids = fields.One2many(comodel_name="linkloving.timesheet.order",
                                          inverse_name="picking_id",
                                          string=u"工时单",
                                          required=False,
                                          )
    state = fields.Selection(selection_add=[('secondary_operation', u'二次加工中'),
                                            ('secondary_operation_done', u'二次加工完成')])

    timesheets_count = fields.Integer(compute='_compute_timesheets_count', string=u'工时单')

    @api.multi
    def _compute_timesheets_count(self):
        for pick in self:
            pick.timesheets_count = len(pick.timesheet_order_ids)

    def action_view_timesheet_order_ids(self):

        return {
            'name': u'工时单',
            'type': 'ir.actions.act_window',
            'res_model': 'linkloving.timesheet.order',
            'view_mode': 'tree,form',
            'view_type': 'form',
            # 'res_id': self.timesheet_order_ids.ids,
            'target': 'current',
            'domain': [('id', 'in', self.timesheet_order_ids.ids)]
        }

    def action_assign_secondary_operation_partner(self):
        return {
            'name': u'分配二次加工负责人',
            'type': 'ir.actions.act_window',
            'res_model': 'linkloving.timesheet.order',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('linkloving_timesheets.view_assign_timesheet_partner').id,
            # 'views': [(False, 'tree'), (self.env.ref('linkloving_timesheets.view_assign_timesheet_partner').id, 'form')],
            'target': 'new',
            'context': {'default_picking_id': self.id}
        }

    def action_view_running_timesheet(self):
        res_id = self.timesheet_order_ids.filtered(lambda x: x.state == 'running')
        if res_id:
            return {
                'name': u'填写二次加工工时',
                'type': 'ir.actions.act_window',
                'res_model': 'linkloving.timesheet.order',
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': self.env.ref('linkloving_timesheets.view_assign_timesheet_partner').id,
                # 'views': [(False, 'tree'), (self.env.ref('linkloving_timesheets.view_assign_timesheet_partner').id, 'form')],
                'target': 'new',
                'res_id': res_id.id,
            }
        else:
            raise UserError(u'未找到对应的工时单')


class linkloving_timesheet_order(models.Model):
    _name = 'linkloving.timesheet.order'

    name = fields.Char('Name', index=True, required=True, )
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    from_partner = fields.Many2one('res.partner', string=u'由谁分配', default=lambda self: self.env.user.partner_id)
    to_partner = fields.Many2one('res.partner', string=u'加工负责人')
    hour_spent = fields.Float(string=u'工时(小时)')
    work_type_id = fields.Many2one(comodel_name='work.type', string=u'工种')

    order_time = fields.Datetime(string=u'开始时间', default=fields.datetime.now())

    state = fields.Selection(string=u"状态", selection=[('draft', u'草稿'),
                                                      ('running', u'进行中'),
                                                      ('done', u'完成'), ], required=False,
                             default='draft')

    picking_id = fields.Many2one('stock.picking', string=u'调拨单')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "单号必须唯一"),
    ]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('linkloving.timesheet.order') or 'New'
        return super(linkloving_timesheet_order, self).create(vals)

    def action_assign_partner(self):
        if len(self.picking_id.timesheet_order_ids.filtered(lambda x: x.state == 'running')) > 1:
            raise UserError(u'已经有一个运行中的工时单')
        if self.state == 'draft':
            self.state = 'running'
            self.picking_id.state = "secondary_operation"
        else:
            raise UserError(u'状态异常')

    def action_assign_hour_spent(self):
        if self.state == 'running':
            self.state = 'done'
            self.picking_id.state = "secondary_operation_done"
        else:
            raise UserError(u'状态异常')
