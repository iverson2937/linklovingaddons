# -*- coding: utf-8 -*-
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

STATUS_OK = 1
STATUS_ERROR = -1
class NameCardController(http.Controller):
    @http.route('/linkloving_oa_api/get_company_by_id/', auth='none', type='json')
    def get_company_by_id(self, **kwargs):
        # db = request.jsonrequest["db"]
        company_id = request.jsonrequest.get("company_id")

        partner = request.env["res.partner"].sudo().browse(company_id)
        if partner:  # 如果有代表重复了
            partner_json = {
                "partner_id": partner.id,
                "name": partner.name,
                "phone": partner.phone or '',
                "level": partner.level,
                "star_cnt": partner.priority,
                "street": partner.street or '',
                "email": partner.email or '',
                "job_title": partner.function or '',
            }
            if partner.country_id:
                partner_json["country"] = {
                    "country_id": partner.country_id.id,
                    "country_name": partner.country_id.name,
                }
            if partner.source_id:
                partner_json["source"] = {
                    "source_id": partner.source_id.id,
                    "source_name": partner.source_id.name or '',
                }
            if partner.crm_source_id:
                partner_json["crm_source"] = {
                    "crm_source_id": partner.crm_source_id.id,
                    "crm_source_name": partner.crm_source_id.name or '',
                }
            if partner.user_id:
                partner_json["saleman"] = {
                    "saleman_id": partner.user_id.id,
                    "saleman_name": partner.user_id.name or '',
                }
            if partner.team_id:
                partner_json["saleteam"] = {
                    "saleteam_id": partner.team_id.id,
                    "saleteam_name": partner.team_id.name,
                }
            tag_list = []
            for tag in partner.category_id:
                tag_list.append({"tag_id": tag.id,
                                 "tag_name": tag.name})
            partner_json["tag_list"] = tag_list

            product_series = []
            for series in partner.product_series_ids:
                product_series.append({
                    "series_id": series.id,
                    "series_name": series.name,
                })
            return partner_json

    @http.route('/linkloving_oa_api/get_company_by_name/', auth='none', type='json')
    def get_company_by_name(self, **kwargs):
        # db = request.jsonrequest["db"]
        name = request.jsonrequest.get("name")
        if u"有限公司" in name:
            name = name.replace(u"有限公司", "")
        elif u'有限责任公司' in name:
            name = name.replace(u"有限责任公司", "")
        elif u'责任有限公司' in name:
            name = name.replace(u"责任有限公司", "")
        elif u'公司' in name:
            name = name.replace(u"公司", "")

        partners = request.env["res.partner"].sudo().search([("name", "ilike", name), ("is_company", "=", True)])
        if partners:  # 如果有代表重复了
            json_list = []
            for partner in partners:
                json_list.append({
                    "partner_id": partner.id,
                    "name": partner.name,
                })
            return json_list

    @http.route('/linkloving_oa_api/add_partner/', auth='none', type='json')
    def add_partner(self, **kwargs):
        name = request.jsonrequest.get("name")
        company_real_name = company_name = request.jsonrequest.get("company_name")
        company_id = request.jsonrequest.get("company_id")
        saleman_id = request.jsonrequest.get("saleman_id")
        saleteam_id = request.jsonrequest.get("saleteam_id")
        tag_list = request.jsonrequest.get("tag_list")
        star_cnt = request.jsonrequest.get("star_cnt")
        partner_lv = request.jsonrequest.get("partner_lv")
        phone = request.jsonrequest.get("phone")
        street = request.jsonrequest.get("street")
        area = request.jsonrequest.get("area")
        source_id = request.jsonrequest.get("crm_source_id")
        src_id = request.jsonrequest.get("source_id")
        partner_type = request.jsonrequest.get("partner_type")
        email = request.jsonrequest.get("email")
        type = request.jsonrequest.get("type")
        country_id = request.jsonrequest.get("country_id")
        product_series = request.jsonrequest.get("series_ids") or []
        job_title = request.jsonrequest.get("job_title")
        if company_id:
            new_company_id = company_id
        else:
            if u"有限公司" in company_name:
                company_name = company_name.replace(u"有限公司", "")
            elif u'有限责任公司' in company_name:
                company_name = company_name.replace(u"有限责任公司", "")
            elif u'责任有限公司' in company_name:
                company_name = company_name.replace(u"责任有限公司", "")
            elif u'公司' in company_name:
                company_name = company_name.replace(u"公司", "")
            company = request.env["res.partner"].sudo().search([("name", "ilike", company_name)], limit=1)
            if not company:
                company = request.env["res.partner"].sudo().create({
                    "name": company_real_name,
                    "street": street,
                    "level": int(partner_lv),
                    "priority": str(star_cnt),
                    "team_id": saleteam_id,
                    "user_id": saleman_id,
                    "crm_source_id": source_id,
                    "customer": partner_type == "customer",
                    "supplier": partner_type == "supplier",
                    "is_company": True,
                    'source_id': src_id,
                    'country_id': country_id,
                    'product_series_ids': product_series or [],
                })
                company.category_id = [tag_list]

            else:
                company.sudo().write({
                    "name": company_real_name,
                    "street": street,
                    "level": int(partner_lv),
                    "priority": str(star_cnt),
                    "team_id": saleteam_id,
                    "user_id": saleman_id,
                    "crm_source_id": source_id,
                    "customer": partner_type == "customer",
                    "supplier": partner_type == "supplier",
                    "is_company": True,
                    'source_id': src_id,
                    'country_id': country_id,
                    'product_series_ids': product_series or [],
                })
                company.category_id = [tag_list]
            new_company_id = company.id
            # company.company_type = "company"

        partners = request.env["res.partner"].sudo().search([("name", "=", name), ("parent_id", '=', new_company_id)], )
        if partners:
            raise UserError(u"该客户已存在")
        s = request.env["res.partner"].sudo().create({
            "name": name,
            "parent_id": new_company_id,
            "mobile": phone,
            "customer": partner_type == "customer",
            "supplier": partner_type == "supplier",
            "is_company": False,
            "email": email,
            "type": type,
            "user_id": saleman_id,
        })
        if type == 'contact':
            s.write({
                "function": job_title,
            })
        return True

    @http.route('/linkloving_oa_api/get_saleman_list/', auth='none', type='json')
    def get_saleman_list(self, **kwargs):
        sources = request.env["res.users"].sudo().search([])
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

    @http.route('/linkloving_oa_api/get_sources/', auth='none', type='json')
    def get_sources(self, **kwargs):
        sources = request.env["res.partner.source"].sudo().search([])
        json_list = []
        for src in sources:
            json_list.append(
                    {"source_id": src.id,
                     "name": src.name or ''})
        return json_list

    @http.route('/linkloving_oa_api/get_countries/', auth='none', type='json')
    def get_countries(self, **kwargs):
        sources = request.env["res.country"].sudo().search([])
        json_list = []
        for src in sources:
            json_list.append(
                    {"country_id": src.id,
                     "name": src.name or ''})
        return json_list

    @http.route('/linkloving_oa_api/get_product_series/', auth='none', type='json')
    def get_product_series(self, **kwargs):
        sources = request.env["crm.product.series"].sudo().search([])
        json_list = []
        for src in sources:
            json_list.append(
                    {"series_id": src.id,
                     "name": src.name or ''})
        return json_list
