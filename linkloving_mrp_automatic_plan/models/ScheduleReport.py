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
