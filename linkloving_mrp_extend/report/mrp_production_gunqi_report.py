# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MrpGunqiProcessReport(models.AbstractModel):
    _name = 'report.mrp.report_gunqi_process'

    @api.multi
    def render_html(self, docids, data=None):
        docargs = {
            'doc_ids': docids,
            'doc_model': 'mrp.production',
            'docs': self.env['mrp.production'].browse(docids),
            'data': data,
        }
        return self.env['report'].render('linkloving_mrp_extend.mrp_production_gunqi_process_report', docargs)
