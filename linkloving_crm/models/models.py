# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmLead(models.Model):
    _inherit = "crm.lead"
    source = fields.Char(string=u'来源')

    continent = fields.Many2one('crm.continent', string=u'所属大洲')
    express_sample_record = fields.Char(string=u'快递账号')
    interested_in_product = fields.Char(string=u'感兴趣产品')

    communication_identifier = fields.Char(string=u'其他沟通方式')
    qq = fields.Char(string=u'QQ')
    wechat = fields.Char(string=u'微信')
    whatsapp = fields.Char(string=u'WhatsApp')
    skype = fields.Char(string=u'Skype')

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
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'is_company': is_company,
            'type': 'contact'
        }

        values_company = {

            # 'source': self.source,
            # 'interested_in_product': self.interested_in_product,
            'communication_identifier': self.communication_identifier,
            'qq': self.qq,
            'skype': self.skype,
            'whatsapp': self.whatsapp,
            'wechat': self.wechat,
            'continent': self.continent.id,
            'express_sample_record': self.express_sample_record
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


class CrmContinent(models.Model):
    _name = 'crm.continent'

    name = fields.Char(string=u'大洲')
