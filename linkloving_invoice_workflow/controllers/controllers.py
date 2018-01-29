# -*- coding: utf-8 -*-
from xls_export_func import account_invoice_export
from odoo.http import content_disposition, dispatch_rpc, request, Controller, route


class ExportReport(Controller):

    @route('/export/account_invoice', type='http', auth='public', csrf=False)
    def account_invoice(self, values):
        filename, data = account_invoice_export(values)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])
