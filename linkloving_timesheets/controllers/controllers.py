# -*- coding: utf-8 -*-
from linklovingaddons.linkloving_app_api.controllers.controllers import LinklovingAppApi, STATUS_CODE_OK
from linklovingaddons.linkloving_app_api.models import JsonResponse
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class LinklovingTimesheets(http.Controller):
    # 分配二次加工负责人
    @http.route('/linkloving_timesheets/action_assign_secondary_operation_partner', type='json', auth='none',
                csrf=False)
    def action_assign_secondary_operation_partner(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        to_partner = request.jsonrequest.get("to_partner")

        if not to_partner or not picking_id:
            raise UserError(u"缺少必要的参数")
        picking = request.env['stock.picking'].sudo(LinklovingAppApi.CURRENT_USER()).browse(int(picking_id))
        if picking.timesheet_order_ids.filtered(lambda x: x.state == 'running'):
            raise UserError(u'已经有一个运行中的工时单')
        sheet = request.env["linkloving.timesheet.order"].sudo(LinklovingAppApi.CURRENT_USER()).create({
            'picking_id': picking_id,
            'to_partner': to_partner,
        })
        sheet.action_assign_partner()

        return JsonResponse.send_response(STATUS_CODE_OK, res_data={})

    # 分配二次加工负责人
    @http.route('/linkloving_timesheets/action_assign_hour_spent', type='json', auth='none', csrf=False)
    def action_assign_hour_spent(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        sheet_id = request.jsonrequest.get("sheet_id")
        work_type_id = request.jsonrequest.get("work_type_id")
        hour_spent = request.jsonrequest.get("hour_spent")

        if not sheet_id or not picking_id or not work_type_id or not hour_spent:
            raise UserError(u"缺少必要的参数")

        sheet = request.env["linkloving.timesheet.order"].sudo(LinklovingAppApi.CURRENT_USER()).browse(sheet_id)
        if sheet_id.picking_id.id != picking_id:
            raise UserError(u'工时单与调拨单不对应,请重试')
        sheet.write({
            'work_type_id': work_type_id,
            'hour_spent': hour_spent,
        })
        sheet.action_assign_hour_spent()

        return JsonResponse.send_response(STATUS_CODE_OK, res_data={})
