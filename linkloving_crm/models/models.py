# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools
from odoo.exceptions import UserError

AVAILABLE_PRIORITIES = [
    ('0', 'badly'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
    ('5', 'top level'),

]


class CrmLead(models.Model):
    _inherit = "crm.lead"

    crm_source_id = fields.Many2one('crm.lead.source', string=u'来源')

    continent = fields.Many2one('crm.continent', string=u'所属大洲')
    express_sample_record = fields.Char(string=u'快递账号')

    interested_in_product = fields.Many2many('product.template', 'crm_interested_in_product_template_ref',
                                             string=u'感兴趣产品')

    product_series_ids = fields.Many2many('crm.product.series', 'crm_product_series_product_template_ref',
                                          string=u'感兴趣系列')

    communication_identifier = fields.Char(string=u'其他沟通方式')
    qq = fields.Char(string=u'QQ')
    wechat = fields.Char(string=u'微信')
    whatsapp = fields.Char(string=u'WhatsApp')
    skype = fields.Char(string=u'Skype')

    mutual_rule_id = fields.Integer()

    lead_price_sheet = fields.Boolean(string=u'产品报价单')

    @api.multi
    def _lead_create_contact(self, name, is_company, parent_id=False, customer=False):
        """ extract data from lead to create a partner
            :param name : furtur name of the partner
            :param is_company : True if the partner is a company
            :param parent_id : id of the parent partner (False if no parent)
            :returns res.partner record
        """
        email_split = tools.email_split(self.email_from)
        values = {

            # 'source': self.source,
            # 'interested_in_product': self.interested_in_product,

            'name': name,
            'user_id': self.user_id.id,
            'comment': self.description,
            'team_id': self.team_id.id,
            'customer': customer,
            'parent_id': parent_id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': email_split[0] if email_split else False,
            'fax': self.fax,
            'title': self.title.id,
            'function': self.function,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'crm_source_id': self.crm_source_id.id,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'is_company': is_company,
            'type': 'contact',
            'priority': self.priority
        }

        from .res_partner import select_company
        if is_company:
            if select_company(self, values, 'name'):
                raise UserError(u'此名称已绑定公司，请确认')
            if select_company(self, values, 'email'):
                raise UserError(u'此Email已绑定公司，请更换')

        alarm_record = set()
        alarm_record1 = set()

        [alarm_record.add(adc.id) for adc in self.interested_in_product]
        [alarm_record1.add(adc.id) for adc in self.product_series_ids]

        print list(alarm_record)
        values_company = {

            'communication_identifier': self.communication_identifier,
            'qq': self.qq,
            'skype': self.skype,
            'whatsapp': self.whatsapp,
            'wechat': self.wechat,
            'continent': self.continent.id,
            'express_sample_record': self.express_sample_record,
            'interested_in_product': [(6, 0, list(alarm_record))],
            'product_series_ids': [(6, 0, list(alarm_record1))],
            'mutual_rule_id': self.mutual_rule_id
        }

        if is_company:
            values = dict(values, **values_company)

        return self.env['res.partner'].create(values)

    @api.multi
    def _create_lead_partner(self):
        """ Create a partner from lead data
            :returns res.partner record
        """
        contact_name = self.contact_name
        if not contact_name:
            contact_name = self.env['res.partner']._parse_partner_name(self.email_from)[0] if self.email_from else False

        is_contact = False
        if self.partner_name:
            partner_company = self._lead_create_contact(self.partner_name, True, False, True)
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            partner_company = None
            is_contact = True

        if contact_name:
            return self._lead_create_contact(contact_name, is_contact, partner_company.id if partner_company else False,
                                             True)

        if partner_company:
            return partner_company
        return self._lead_create_contact(self.name, True, False, True)

    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Rating', index=True,
                                default=AVAILABLE_PRIORITIES[0][0])

    @api.multi
    def action_tree_list_view(self):

        domain = [('crm_product_type', '=', 'brand')]
        brand_data = self.env['crm.product.series'].search(domain)

        msg_data_my = [
            {'name': brand_data_one.name,
             'code': brand_data_one.id,
             'type': brand_data_one.crm_product_type,
             'icon': 'icon-th',
             'child': [
                 {
                     'name': series_data_one.name,
                     'code': series_data_one.id,
                     'type': series_data_one.crm_product_type,
                     'icon': 'icon-minus-sign',
                     'parentCode': series_data_one.crm_Parent_id.id,
                     'child': [
                         {
                             'name': version_data_one.name,
                             'code': version_data_one.id,
                             'type': version_data_one.crm_product_type,
                             'icon': '',
                             'parentCode': version_data_one.crm_Parent_id.id,
                             'child': []}
                         for version_data_one in series_data_one.crm_Parent_ontomany_ids]}
                 for series_data_one in brand_data_one.crm_Parent_ontomany_ids]}
            for brand_data_one in brand_data]

        return {
            'type': 'ir.actions.client',
            'tag': 'crm_tree_list_js',
            'products_data': msg_data_my,
            'leads_id': self.id,
            'model_lead_partner': 'crm.lead',
        }

    @api.model
    def add_partner_to_lead(self, id_one, version_list, models_view):
        res = self.env['res.partner'].browse(id_one)
        if models_view == 'crm.lead':
            res = self.env['crm.lead'].browse(id_one)
        # res_reuslt = res.write({'product_series_ids': [(6, 0, version_list)]})
        res_reuslt = res.write({'product_series_ids': [(4, version_one) for version_one in version_list]})

        if res_reuslt:
            return 'ok'
        else:
            raise UserError(u'操作失败')


class CrmContinent(models.Model):
    _name = 'crm.continent'

    name = fields.Char(string=u'大洲')
