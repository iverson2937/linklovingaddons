# -*- coding: utf-8 -*-
# from linklovingaddons.linkloving_app_api.controllers.controllers import STATUS_CODE_OK, JsonResponse
# from odoo import http
# from odoo.http import request
#
#
# class LinklovingMrpAutomaticPlan(http.Controller):
#     @http.route('/linkloving_app_api/mrp_equipment/list', type='json', auth='none', csrf=False)
#     def mrp_equipment_list(self):
#         process_id = request.jsonrequest.get("process_id")
#         euip = request.env["mrp.equipment"].sudo().search_read([("process_id", "=", process_id)])
#         return JsonResponse.send_response(STATUS_CODE_OK, res_data=euip)
