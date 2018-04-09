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
        sub_companies = self.env["res.partner"].sudo().search([('sub_company', '=', 'sub')])
        pos = self.env["purchase.order"].sudo().search([('partner_id', 'in', sub_companies.ids),
                                                 ('state', '=', 'purchase')])

        report_vals = []
        for po in pos:
            if po.picking_ids.filtered(lambda x: x.state not in ["done", "cancel"]):  # 如果收货未完成了
                report_vals.append(self.prepare_report_vals(po))

        return report_vals

    @api.model
    def get_sub_company_report(self, **kwargs):
        so_id = kwargs.get("so_id")
        so = self.env["sale.order"].sudo().browse(int(so_id))
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
        process = self.env["mrp.process"].sudo().search_read([("company_id", "=", self.env.user.company_id.id)],
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
            'sub_so_name': {
                'id': po.so_id_from_sub or 0,
                'name': po.so_name_from_sub or '',
                'model': 'sale.order',
                'sub_ip': po.partner_id.sub_company_id.host_correct or '',  # 子系统的ip地址 用于跳转
            },
            'report_remark': po.report_remark or '',
            'shipping_rate': str(round(po.shipping_rate, 2)) + '%' or '0.00%',
            'handle_date': po.handle_date,
        }
        if po.first_so_number:
            so_order = self.env["sale.order"].sudo().search([('name', '=', po.first_so_number)], limit=1)
            manual_order = self.env["manual.procurement.order"].sudo().search([('name', '=', po.first_so_number)],
                                                                              limit=1)
            if so_order:
                data.update({
                    'so': self.prepare_order_info(so_order),
                    'pi_number': so_order.pi_number or '',
                    'partner': so_order.partner_id.name or '',
                    'sale_man': so_order.user_id.name or '',
                })
            elif manual_order:
                res_partner = self.env["res.partner"].sudo().search([('sub_company', '=', "main")], limit=1)
                data.update({
                    'so': self.prepare_order_info(manual_order),
                    'pi_number': manual_order.alia_name or '',
                    'partner': res_partner.name or '',
                    'handle_date': manual_order.date_excepted,
                    'sale_man': manual_order.create_uid.name or '',
                })
        return data

    def save_report_remark(self, **kwargs):
        report_remark = kwargs['report_remark']



class PurchaseOrderInherit(models.Model):
     _inherit = 'purchase.order'
     report_remark = fields.Char(string=u'备注')
     
     @api.multi
     def write(self, vals):
         return super(PurchaseOrderInherit, self).write(vals)

     @api.multi
     def sudo_write(self, vals):
         return self.sudo().write(vals)
