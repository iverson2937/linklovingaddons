# -*- coding: utf-8 -*-
from odoo import models,api,_


class ReportPaymentApplication(models.AbstractModel):
    _name = 'report.payment.application'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('linkloving_account.report_payment_application')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self.id),
        }
        print self.env[report.model].browse(self.id)
        return report_obj.render('linkloving_account.report_payment_application', docargs)
