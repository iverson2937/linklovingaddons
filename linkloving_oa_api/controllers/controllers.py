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

    @http.route('/linkloving_oa_api/add_partner/', auth='none', type='json')
    def add_partner(self, **kwargs):
        name = request.jsonrequest.get("name")
        company_name = request.jsonrequest.get("company_name")
        saleman_id = request.jsonrequest.get("saleman_id")
        saleteam_id = request.jsonrequest.get("saleteam_id")
        tag_list = request.jsonrequest.get("tag_list")
        star_cnt = request.jsonrequest.get("star_cnt")
        partner_lv = request.jsonrequest.get("partner_lv")
        crm_source_id = request.jsonrequest.get("crm_source_id")

        partners = request.env["res.partner"].sudo().search([("name", "ilike", name)])
        if partners:
            return {"error": u"该客户已存在"}
        else:
            request.env["res.partner"].sudo().create({

            })
            return

    @http.route('/linkloving_oa_api/get_saleman_list/', auth='none', type='json')
    def get_saleman_list(self, **kwargs):
        sources = request.env["res.partner"].sudo().search([('employee', '=', True)])
        json_list = []
        for src in sources:
            json_list.append(
                    {"partner_id": src.id,
                     "name": src.name or ''})
        return json_list

    @http.route('/linkloving_oa_api/get_saleteam_list/', auth='none', type='json')
    def get_saleteam_list(self, **kwargs):
        sources = request.env["crm.team"].sudo().search([])
        json_list = []
        for src in sources:
            json_list.append(
                    {"team_id": src.id,
                     "name": src.name or ''})
        return json_list

    @http.route('/linkloving_oa_api/get_partner_tag_list/', auth='none', type='json')
    def get_partner_tag_list(self, **kwargs):
        sources = request.env["res.partner.category"].sudo().search([])
        json_list = []
        for src in sources:
            json_list.append(
                    {"category_id": src.id,
                     "name": src.name or ''})
        return json_list

    @http.route('/linkloving_oa_api/get_origins/', auth='none', type='json')
    def get_origins(self, **kwargs):
        sources = request.env["crm.lead.source"].sudo().search([])
        json_list = []
        for src in sources:
            json_list.append(
                    {"src_id": src.id,
                     "name": src.name or ''})
        return json_list
