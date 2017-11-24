# -*- coding: utf-8 -*-
from linklovingaddons.linkloving_app_api.controllers.controllers import STATUS_CODE_OK, JsonResponse, LinklovingAppApi
from odoo import http
from odoo.http import request


class LinklovingOutsourceAppApi(http.Controller):
    @http.route('/linkloving_app_api/get_outsourcing_order_by_state', type='json', auth="none", csrf=False, )
    def get_outsourcing_order_by_state(self, **kw):
        state = request.jsonrequest.get("state")
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")

        orders = request.env["outsourcing.process.order"].sudo().search_read([("state", "=", state)],
                                                                             limit=limit,
                                                                             offset=offset)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=orders)

    @http.route('/linkloving_app_api/change_outsourcing_order_state', type='json', auth="none", csrf=False, )
    def change_outsourcing_order_state(self, **kw):
        order_id = request.jsonrequest.get("order_id")
        qty_produced = request.jsonrequest.get("qty_produced")
        state = request.jsonrequest.get("state")
        # offset = request.context.get("offset")

        order = request.env["outsourcing.process.order"].sudo(LinklovingAppApi.CURRENT_USER()).browse(order_id)
        order.qty_produced = qty_produced
        if state == 'draft_to_out_ing':
            order.action_draft_to_out()
        elif state == 'out_ing_to_done':
            order.action_out_to_done()

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=order.read())
