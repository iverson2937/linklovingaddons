# -*- coding: utf-8 -*-
import json
import calendar
import time

from odoo import models, fields, api
from odoo import tools
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date

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

    lead_is_quote = fields.Boolean(string=u'已报价', default=False)
    lead_is_sample = fields.Boolean(string=u'已寄样', default=False)
    lead_is_follow_up = fields.Boolean(string=u'已跟进', default=False)

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

    @api.model
    def retrieve_sales_dashboard(self):
        res = super(CrmLead, self).retrieve_sales_dashboard()

        new_res = {
            'basic_information': {
                'all_lead_partner': 0,
                'all_latent_partner': 0,
                'all_partner': 0,
                'all_opportunity': 0,
            },
            'follow_up': {
                'all_follow_record': 0,
                'all_partner_follow_record': 0,
                'all_quote_cont': 0,
                'all_sample_cont': 0,
            },
            'new_message': {
                'new_lead_partner': 0,
                'new_latent_partner': 0,
                'new_partner': 0,
                'new_lead': 0,
            },
            'sale_order': {
                'self_sale_amount_total': 0,
                'self_year_sale_amount_total': 0,
                'target_sales_year': 0,
                'target_sales_year_finishing_rate': '',
            },
            'invoiced_my': {
                'this_year': 0,
                'this_invoiced_month': 0,
            },
            'won_this_month': 0,
            'is_manage': 0,
            'char_data': '',
            'is_show_custom_module': 0,
            'salesman_name_list': [],

        }

        day_now = time.localtime()
        day_begin = '%d-%02d-01' % (day_now.tm_year, day_now.tm_mon)  # 月初肯定是1号
        wday, monthRange = calendar.monthrange(day_now.tm_year, day_now.tm_mon)  # 得到本月的天数 第一返回为月第一日为星期几（0-6）, 第二返回为此月天数
        day_end = '%d-%02d-%02d' % (day_now.tm_year, day_now.tm_mon, monthRange)
        year_begin = '%d-01-01' % (day_now.tm_year)
        now_day = '%d-%02d-%02d' % (day_now.tm_year, day_now.tm_mon, day_now.tm_mday)

        # 基础信息
        domain_all = [('customer', '=', '1'), ('is_company', '=', True)]
        all_lead_partner = self.env['res.partner'].search(domain_all + [('crm_is_partner', '=', True),
                                                                        ('public_partners', '!=', 'public')])
        new_res['basic_information']['all_lead_partner'] = len(all_lead_partner)

        all_latent_partner = self.env['res.partner'].search(
            domain_all + [('is_order', '=', False), ('crm_is_partner', '=', False),
                          ('public_partners', '!=', 'public')])
        new_res['basic_information']['all_latent_partner'] = len(all_latent_partner)

        all_partner = self.env['res.partner'].search(
            domain_all + [('is_order', '=', True), ('crm_is_partner', '=', False), ('public_partners', '!=', 'public')])
        new_res['basic_information']['all_partner'] = len(all_partner)

        all_opportunity = self.search([('type', '=', 'opportunity')])
        new_res['basic_information']['all_opportunity'] = len(all_opportunity)

        # 跟进信息

        all_partner_follow = self.env['res.partner'].search(
            domain_all + [('customer_follow_up_date', '>=', now_day)])

        new_res['follow_up']['all_partner_follow_record'] += len(all_partner_follow)

        for opp in all_opportunity:
            # Expected closing
            if opp.message_ids:
                for msg in opp.message_ids:

                    date_msg_record = fields.Date.from_string(msg.create_date)
                    # quote_id = self.env['message.label'].search([('name', 'ilike', '报价')])
                    # sample_id = self.env['message.label'].search([('name', 'ilike', '送样')])
                    quote_id = self.env.ref('linkloving_crm.message_label_quote_id1')
                    sample_id = self.env.ref('linkloving_crm.message_label_sample_id')

                    if date_msg_record == date.today() and msg.message_type != 'notification':
                        new_res['follow_up']['all_follow_record'] += 1
                        if quote_id.id in msg.messages_label_ids.ids:
                            new_res['follow_up']['all_quote_cont'] += 1
                        elif sample_id.id in msg.messages_label_ids.ids:
                            new_res['follow_up']['all_sample_cont'] += 1

                            # if date.today() <= date_msg_record <= date.today() + timedelta(days=7):
                            #     new_res['closing']['next_7_days'] += 1
                            # if date_msg_record < date.today():
                            #     new_res['closing']['overdue'] += 1
            if opp.date_closed:
                date_closed = fields.Date.from_string(opp.date_closed)
                if date.today().replace(day=1) <= date_closed <= date.today():
                    if opp.planned_revenue:
                        new_res['won_this_month'] += opp.planned_revenue
                if fields.Date.from_string(year_begin) <= date_closed:
                    if opp.planned_revenue:
                        res['won']['last_month'] = opp.planned_revenue

        # 新增信息
        data_partner = [all_lead_partner, all_latent_partner, all_partner, all_opportunity]
        key_partner = ['new_lead_partner', 'new_latent_partner', 'new_partner', 'new_lead']
        for val in range(0, len(data_partner)):
            for lead_partner_one in data_partner[val]:
                date_lead_partner = fields.Date.from_string(lead_partner_one.create_date)
                if date_lead_partner == date.today():
                    new_res['new_message'][key_partner[val]] += 1

        if self.env.ref(
                'sales_team.group_sale_manager').id in self.env.user.groups_id.ids or self.env.user.sale_team_id.user_id == self.env.user:
            new_res['is_manage'] = 1

        data_list = []
        data_team_list = []
        data_team_name_list = []
        data_manage_team_name_list = self.env['res.users']  # 管理员 为给个 销售团队主管分配目标  列表
        domain_salesman = [('state', '=', 'sale'), ('create_date', '<=', day_end)]

        account_invoice_domain = [
            ('state', 'in', ['open', 'paid']),
            ('type', 'in', ['out_invoice', 'out_refund'])
        ]

        all_salesman_team = self.env['res.users']

        if self.env.ref('sales_team.group_sale_manager').id in self.env.user.groups_id.ids:
            invoice_data = self.env['account.invoice'].search_read(account_invoice_domain + [('date', '>=', day_begin)],
                                                                   ['date', 'amount_untaxed_signed'])
            for invoice in invoice_data:
                new_res['invoiced_my']['this_invoiced_month'] += invoice['amount_untaxed_signed']

            account_invoice_domain += [('date', '>=', year_begin)]

            for team_one in self.env['crm.team'].search([]):
                all_salesman_team += team_one.member_ids
                data_team_name_list.append(team_one.name)
                team_sale_sum = 0

                data_manage_team_name_list += team_one.user_id

                for team_user_one in team_one.member_ids:

                    sale_order_list = self.env['sale.order'].sudo().search(
                        domain_salesman + [('user_id', '=', team_user_one.id), ('create_date', '>=', day_begin)])
                    for sale_one in sale_order_list:
                        team_sale_sum += sale_one.amount_total
                data_team_list.append(team_sale_sum)

        else:
            # 根据用户获取销售团队 然后再除去团队管理者
            # all_salesman_team = self.env.user.sale_team_id.member_ids - self.env.user.sale_team_id.user_id
            # 不取出团队管理者
            all_salesman_team = self.env.user.sale_team_id.member_ids

            # 这是过滤销售团队里面 权限为所有文档的人
            # for new_salesman_one in all_salesman_team:
            #     if self.env.ref('sales_team.group_sale_salesman_all_leads').id in new_salesman_one.groups_id.ids:
            #         all_salesman_team -= new_salesman_one

            if self.env.user.sale_team_id.user_id != self.env.user:
                account_invoice_domain += [('date', '>=', year_begin), ('user_id', '=', self.env.uid)]
            else:
                account_invoice_domain += [('date', '>=', year_begin),
                                           ('user_id', 'in', [ad.id for ad in all_salesman_team])]

        invoice_data_year = self.env['account.invoice'].search_read(account_invoice_domain,
                                                                    ['date', 'amount_untaxed_signed'])

        for invoice_year in invoice_data_year:
            new_res['invoiced_my']['this_year'] += invoice_year['amount_untaxed_signed']

        # state= sale
        year_sale_sum = 0  # 团队成员 年总销售金额 与 团队主管 销售金额
        year_sale_sum_temporary = 0

        if self.env.ref('sales_team.group_sale_manager').id in self.env.user.groups_id.ids:
            sale_order_man_list = self.env['sale.order'].search(domain_salesman + [('create_date', '>=', year_begin)])
            for sale_one_man in sale_order_man_list:
                year_sale_sum_temporary += sale_one_man.amount_total
            sale_order_man_month_list = self.env['sale.order'].search(
                domain_salesman + [('create_date', '>=', day_begin)])
            for sale_one_month_man in sale_order_man_month_list:
                new_res['sale_order']['self_sale_amount_total'] += sale_one_month_man.amount_total
        else:
            for team_user_one in all_salesman_team:
                sale_sum = 0
                sale_order_list = self.env['sale.order'].sudo().search(
                    domain_salesman + [('user_id', '=', team_user_one.id), ('create_date', '>=', day_begin)])
                for sale_one in sale_order_list:
                    sale_sum += sale_one.amount_total
                data_list.append(sale_sum)

                if team_user_one == self.env.user:
                    new_res['sale_order']['self_sale_amount_total'] = sale_sum
                    year_sale_order_list = self.env['sale.order'].search(domain_salesman +
                                                                         [('user_id', '=', team_user_one.id),
                                                                          ('create_date', '>=', year_begin)])
                    for year_sale_one in year_sale_order_list:
                        year_sale_sum += year_sale_one.amount_total

        if self.env.user.sale_team_id.user_id == self.env.user:
            #     团队管理员
            year_sale_sum_charge = 0
            year_sale_order_list = self.env['sale.order'].search(
                domain_salesman + [('user_id', 'in', [ad.id for ad in all_salesman_team]),
                                   ('create_date', '>=', year_begin)])
            for year_sale_one in year_sale_order_list:
                year_sale_sum_charge += year_sale_one.amount_total
            year_sale_sum = year_sale_sum_charge

            invoice_data = self.env['account.invoice'].search_read(account_invoice_domain + [('date', '>=', day_begin),
                                                                                             ('user_id', 'in',
                                                                                              [ad.id for ad in
                                                                                               all_salesman_team])],
                                                                   ['date', 'amount_untaxed_signed'])
            for invoice in invoice_data:
                new_res['invoiced_my']['this_invoiced_month'] += invoice['amount_untaxed_signed']

        if self.env.user.sale_team_id.user_id == self.env.user and self.env.ref(
                'sales_team.group_sale_manager').id not in self.env.user.groups_id.ids:
            new_res['sale_order']['self_sale_amount_total'] = sum(data_list)

        new_res['sale_order'][
            'self_year_sale_amount_total'] = year_sale_sum if year_sale_sum > 0 else year_sale_sum_temporary

        new_res['salesman_name_list'] = [{'name': str(team_user_one.name), 'id': team_user_one.id,
                                          'target_sales_year': team_user_one.target_sales_year,
                                          'target_sales_invoiced': team_user_one.target_sales_invoiced,
                                          'target_sales_won': team_user_one.target_sales_won} for team_user_one in (
                                             data_manage_team_name_list if data_manage_team_name_list else self.env.user.sale_team_id.member_ids)]

        char_data = {
            'labels': data_team_name_list if data_team_name_list else [str(team_user_one.name) for team_user_one in
                                                                       all_salesman_team],
            'datasets': [{
                'label': '销售额(¥)',
                'data': data_team_list if data_team_list else data_list,
                'backgroundColor': ['rgba(54, 162, 235, 0.2)'] * len(all_salesman_team),
                'borderWidth': 1
            }]
        }
        if self.env.user.sale_team_id or self.env.ref(
                'sales_team.group_sale_manager').id in self.env.user.groups_id.ids:
            new_res['is_show_custom_module'] = 1

        new_res['sale_order']['target_sales_year'] = self.env.user.target_sales_year

        if self.env.user.target_sales_year > 0:
            new_res['sale_order']['target_sales_year_finishing_rate'] = str(
                round((new_res['sale_order']['self_year_sale_amount_total'] / self.env.user.target_sales_year) * 100, 2)
            ) + '%'

        new_res['char_data'] = json.dumps(char_data)

        return dict(res, **new_res)

        # def sum_sale_total(self, domain):
        #     sale_sum = 0
        #     sale_order_list = self.env['sale.order'].sudo().search(
        #         [('user_id', '=', team_user_one.id), ('create_date', '>', day_begin), ('create_date', '<', day_end)])
        #     for sale_one in sale_order_list:
        #         sale_sum += sale_one.amount_total


class CrmContinent(models.Model):
    _name = 'crm.continent'

    name = fields.Char(string=u'大洲')


class CrmCrmTeam(models.Model):
    _inherit = "crm.team"

    @api.multi
    def write(self, vals):

        if vals.get('user_id'):
            team_master = self.env['res.users'].browse(int(vals.get('user_id')))
            team_master.write({'sale_team_id': self.id})
        else:
            if self.user_id:
                self.user_id.write({'sale_team_id': False})

        res = super(CrmCrmTeam, self).write(vals)
        return res


class CrmSaleDaily(models.Model):
    _name = 'crm.sale.daily'

    @api.model
    def _shenheren(self):
        # self.env['res.partner'].search([('id', 'in', (3624, 3455))])
        partner_list = self.env.user.sale_team_id.user_id

        return partner_list

    name = fields.Char(string=u'名称')
    summit_time = fields.Date(string=u'时间', default=fields.Datetime.now)
    type = fields.Selection([('day_daily', u'日报'), ('week_daily', u'周报'), ('mouth_daily', u'月报')], string=u'类型')
    summary = fields.Html(string=u'总结')
    plan = fields.Text(string=u'计划')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    approval_man_ids = fields.Many2many("res.users", string=u'提交给...审核', default=_shenheren)

    @api.multi
    def set_daily_save(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def create(self, vals):
        user_name = ''
        if vals.get('type'):
            if vals.get('type') == 'day_daily':
                user_name = '日报'
            elif vals.get('type') == 'week_daily':
                user_name = '周报'
            elif vals.get('type') == 'mouth_daily':
                user_name = '月报'

        vals['team_id'] = self.env.user.sale_team_id.id

        vals['name'] = self.env.user.name + user_name
        return super(CrmSaleDaily, self).create(vals)


class CrmResUsers(models.Model):
    _inherit = 'res.users'

    target_sales_year = fields.Integer(u'年目标')

    @api.model
    def set_salesman_target(self, data):
        print data

        for salesman_one in data:
            sale_user = self.env['res.users'].browse(int(salesman_one.get('id')))

            sale_user.sudo().write({'target_sales_won': int(salesman_one.get('opportunity_name')) if salesman_one.get(
                'opportunity_name') else False,
                                    'target_sales_invoiced': int(salesman_one.get('order_name')) if salesman_one.get(
                                        'order_name') else False,
                                    'target_sales_year': int(salesman_one.get('year_order_name')) if salesman_one.get(
                                        'year_order_name') else False})

        return 'ok'
