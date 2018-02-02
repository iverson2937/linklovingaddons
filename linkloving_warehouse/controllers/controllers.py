# -*- coding: utf-8 -*-
from xls_export_func import product_template_export
from odoo.http import content_disposition, dispatch_rpc, request, Controller, route


class ExportReport(Controller):

    @route('/export/product_template', type='http', auth='public', csrf=False)
    def product_template(self, values):
        filename, data = product_template_export(values)
        return request.make_response(data, headers=[('Content-Disposition', content_disposition(filename)),
                                                    ('Content-Type', 'application/vnd.ms-excel')])
