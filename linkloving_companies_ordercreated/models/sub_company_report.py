# -*- coding: utf-8 -*-
import json

import requests
from requests import ConnectionError

from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    sub_company = fields.Selection(related='partner_id.sub_company')

    def action_open_sub_company_tranck_report(self):
        return {
            'name': self.name + u'-生产跟踪单',
            'type': 'ir.actions.client',
            'tag': 'sub_company_report',
            'context': {"sub_company_order_track": True,
                        "so_id": self.id
                        }
        }

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

    @api.model
    def get_sub_company_report(self, **kwargs):
        so_id = kwargs.get("so_id")
        so = self.env["sale.order"].browse(int(so_id))
        if not so:
            raise UserError(u'未找到对应的销售单')

        so_data = {
            'company_name': self.env.user.company_id.name or '',
            'so_name': so.name,
            'pi_number': so.pi_name_from_main or '',
            'so_name_from_main': so.so_name_from_main or '',
            'po_from_main': so.po_name_from_main or '',
            'handle_date': so.order_date_from_main or '',
            'follow_partner_name_from_main': so.follow_partner_name_from_main or '',
            'sale_man_from_main': so.sale_man_from_main or '',
            'partner_name_from_main': so.partner_name_from_main or '',
            'processes': self.get_all_process() or [],
            'order_line': self.get_order_line_info(so),
        }
        return so_data

    def get_all_process(self):
        process = self.env["mrp.process"].search_read([("company_id", "=", self.env.user.company_id.id)],
                                                      fields=["name"])
        return process

    def get_order_line_info(self, so):
        vals = []
        for line in so.order_line:
            vals.append({
                'default_code': line.product_id.default_code or '',
                'inner_code': line.product_id.inner_code or '',
                'product_qty': line.product_qty,
            })
        return vals

    def prepare_order_info(self, order):
        return {
            'id': order.id,
            'name': order.name,
            'model': order._name,
        }
    def prepare_report_vals(self, po):
        data = {
            'producer': po.partner_id.sub_company_id.name or '',
            'po': self.prepare_order_info(po),
            'follow_partner': po.partner_id.follow_partner_id.follow_partner_id.name or '',
            'state': po.state,
            'sub_so_name': po.so_name_from_sub or ''
        }
        if po.first_so_number:
            so_order = self.env["sale.order"].search([('name', '=', po.first_so_number)], limit=1)
            manual_order = self.env["manual.procurement.order"].search([('name', '=', po.first_so_number)], limit=1)
            if so_order:
                data.update({
                    'so': self.prepare_order_info(so_order),
                    'pi_number': so_order.pi_number or '',
                    'partner': so_order.partner_id.name or '',
                    'handle_date': so_order.validity_date,
                    'sale_man': so_order.user_id.name or '',
                })
            elif manual_order:
                data.update({
                    'so': self.prepare_order_info(manual_order),
                    'pi_number': manual_order.alia_name or '',
                    'partner': '',
                    'handle_date': manual_order.date_excepted,
                    'sale_man': manual_order.create_uid.name or '',
                })
        return data
