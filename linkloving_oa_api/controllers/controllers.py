# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class LinklovingOaApi(http.Controller):
    @http.route('/linkloving_oa_api/get_company_by_name/', auth='none', type='json')
    def get_company_by_name(self, **kwargs):
        request.session.db = request.jsonrequest["db"]
        request.params["db"] = request.jsonrequest["db"]
        name = request.jsonrequest.get("name")
        if u"有限公司" in name:
            name = name.replace(u"有限公司", "")
        elif u'有限责任公司' in name:
            name = name.replace(u"有限责任公司", "")
        elif u'责任有限公司' in name:
            name = name.replace(u"责任有限公司", "")
        elif u'公司' in name:
            name = name.replace(u"公司", "")

        partners = request.env["res.partner"].sudo().search_read([("name", "ilike", name)], fields=["name"])
        if partners:  # 如果有代表重复了
            return partners

    # @http.route('/linkloving_oa_api/get_origin/', auth='none', type='json', csrf=False)
    # def get_origin(self, **kwargs):
    #     # request.session.db = '0426'#'#request.jsonrequest["db"]
    #     # request.params["db"] = '0426'#request.jsonrequest["db"]
    #     sources = request.env["crm.lead.source"].sudo().search_read([], fields=['name'])
    #     return sources
