# -*- coding: utf-8 -*-
import json

import requests
from requests import ConnectionError

from odoo import models, fields, api
from odoo.exceptions import UserError


class SubCompanyReport(models.Model):
    _name = 'sub.company.report'

    @api.model
    def get_report(self):
        sub_companies = self.env["res.partner"].search([('sub_company', '=', 'sub')])
        pos = self.env["purchase.order"].search([('partner_id', 'in', sub_companies.ids),
                                                 ('state', '=', 'purchase')])
        report_vals = []
        for po in pos:
            if po.picking_ids.filtered(lambda x: x.state not in ["done", "cancel"]):  # 如果收货未完成了
                report_vals.append(self.prepare_report_vals(po))

        return report_vals

    def prepare_report_vals(self, po):
        data = {
            'producer': po.partner_id.sub_company_id.name or '',
            'po_name': po.name,
            'follow_partner': po.partner_id.follow_partner_id.follow_partner_id.name or '',
            'state': po.state,
            'sub_so_name': po.so_name_from_sub or ''
        }
        if po.first_so_number:
            so_order = self.env["sale.order"].search([('name', '=', po.first_so_number)])
            manual_order = self.env["manual.procurement.order"].search([('name', '=', po.first_so_number)])
            if so_order:
                data.update({
                    'so_name': so_order.name or '',
                    'pi_number': so_order.pi_number or '',
                    'partner': so_order.partner_id.name or '',
                    'handle_date': so_order.validity_date,
                    'sale_man': so_order.user_id.name or '',
                })
            elif manual_order:
                data.update({
                    'so_name': manual_order.name or '',
                    'pi_number': manual_order.alia_name or '',
                    'partner': '',
                    'handle_date': manual_order.date_excepted,
                    'sale_man': manual_order.create_uid.name or '',
                })
        return data
