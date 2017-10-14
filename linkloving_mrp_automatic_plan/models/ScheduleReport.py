# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError


class SelectReportWizard(models.TransientModel):
    _name = 'select.report.wizard'

    report_type = fields.Selection(string=u"类型",
                                   selection=[('from_product', u'产品报表'),
                                              ('from_so', u'SO报表'), ],
                                   default='from_product', )

    product_ids = fields.Many2many(comodel_name="product.template", string=u'相关的产品')

    so_ids = fields.Many2many(comodel_name="sale.order", string=u'相关的销售单')

    def action_create_report(self):
        if self.report_type == 'from_so' and self.so_ids:
            return self.acticon_view_report_view()
        if self.report_type == 'from_product' and self.product_ids:
            return self.acticon_view_report_view()

        raise UserError(u"请选择相关产品或销售单")

    def acticon_view_report_view(self):
        return {
            'name': u"报表",
            'type': 'ir.actions.client',
            'tag': 'schedule_production_report',
            'target': 'reload'
        }


class ScheduleReport(models.TransientModel):
    _name = 'schedule.report'
    def do_report(self):
        pass


class MrpReportProductLine(models.Model):
    _name = 'mrp.report.product.line'

    report_id = fields.Many2one(comodel_name="mrp.report", string=u"报告")
    procurement_id = fields.Many2one(comodel_name="procurement.order", string=u"补货单", required=True)
    production_id = fields.Many2one(comodel_name="mrp.production",
                                    string=u"相关制造单",
                                    related="procurement_id.production_id")

    orderpoint_id = fields.Many2one(comodel_name="stock.warehouse.orderpoint", string=u"补货规则")
    order_qty = fields.Float(string=u'数量')
    product_id = fields.Many2one(comodel_name="product.product", string=u"产品", related="orderpoint_id.product_id")


class MrpReport(models.Model):
    _name = 'mrp.report'

    total_orderpoint_count = fields.Integer(string=u"此次运算订货规则个数", readonly=True)
    state = fields.Selection(string=u"完成状态",
                             selection=[('part', u'部分完成,出现异常'), ('done', u'已完成'), ],
                             default="part",
                             required=False,
                             readonly=True,
                             )
    report_type = fields.Selection(string=u"报告类型",
                                   selection=[('stock_report', '备货制报告')],
                                   default="stock_report",
                                   readonly=True, )
    report_line_ids = fields.One2many(comodel_name="mrp.report.product.line",
                                      inverse_name="report_id",
                                      string=u"报告条目",
                                      readonly=True, )
    report_start_time = fields.Datetime(string=u"报告生成时间",
                                        default=fields.Datetime.now(),
                                        readonly=True)

    report_end_time = fields.Datetime(string=u"报告结束时间", readonly=True)

    def prepare_report_line_val(self, procurement_id, report_id, orderpoint_id=None, order_qty=0):
        return {
            'procurement_id': procurement_id.id,
            'report_id': report_id.id,
            'orderpoint_id': orderpoint_id.id,
            'order_qty': order_qty,
        }
