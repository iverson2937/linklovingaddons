# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPickingExtend(models.Model):
    _inherit = 'stock.picking'

    report_remark = fields.Text(string=u'发货报告备注')


class PickingReportWizard(models.Model):
    _name = 'picking.report.wizard'

    start_time = fields.Datetime(string=u'开始时间(交期)')
    end_time = fields.Datetime(string=u'结束时间(交期)', default=fields.Datetime.now())
    sale_team_ids = fields.Many2many(comodel_name="crm.team", string=u"销售团队")

    def action_do_report(self):
        vals = self._prepare_report_vals()
        return {
            'name': self.start_time + ' - ' + self.end_time + u'-仓库发货报表',
            'type': 'ir.actions.client',
            'tag': 'warehouse_picking_report',
            'context': {"vals": vals,}
        }

    def _prepare_report_vals(self):
        if self.sale_team_ids:
            domain = [('team_id', 'in', self.sale_team_ids.ids),
                      ('validity_date', '>=', self.start_time),
                      ('validity_date', '<', self.end_time),
                      ('state', 'in', ['sale', 'done'])]
        else:
            domain = [('validity_date', '>=', self.start_time),
                      ('validity_date', '<', self.end_time),
                      ('state', 'in', ['sale', 'done'])]
        orders = self.env["sale.order"].search(domain)

        vals = []
        for order in orders:
            picking_to_do = order.picking_ids.filtered(lambda x: x.state not in ["done", "cancel"])
            picking_list = []
            for picking in order.picking_ids:
                picking_list.append({
                    'id': picking.id,
                    'name': picking.name,
                    'model': picking._name,
                    'state': picking.state,
                    'number_of_packages': picking.number_of_packages or 0,
                    'report_remark': picking.report_remark or '',
                    'carrier_id': {
                        'id': picking.carrier_id.id,
                        'name': picking.carrier_id.name or '',
                        'model': picking.carrier_id._name,
                    } if picking.carrier_id else {},
                    'back_order_id': {
                        'id': picking.backorder_id.id,
                        'name': picking.backorder_id.name,
                        'model': picking.backorder_id._name,
                    } if picking.backorder_id else {},
                    # 'delivery_partner_id': {
                    #
                    # }
                })
            vals.append({
                'id': order.id,
                'name': order.name,
                'partner_name': order.partner_id.name,
                'is_done': False if picking_to_do else True,
                'model': order._name,
                'pickings': picking_list
            })

        return vals
