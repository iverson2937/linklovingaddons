# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from datetime import date, time, datetime, timedelta
from odoo import fields, api, models
from odoo.exceptions import UserError
from odoo import tools, _
from odoo.modules.module import get_module_resource
from string import lower
import re

AVAILABLE_PRIORITIES = [
    ('0', 'badly'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
    ('5', 'top level'),
]


def select_company(my_self, vals, type):
    strip_str = vals.get(type)

    if my_self._name == 'crm.lead' and type == 'email':
        type = 'email_from'
    if strip_str != (my_self[type] if my_self else ''):
        if strip_str:
            result = my_self.env['res.partner'].search(
                [(type, '=', strip_str.strip()), ('customer', '=', True),
                 ('is_company', '=', True)])
            return result


def action_crm_channel(my_self, body):
    my_self.env['mail.channel'].search([('name', '=', '公海通知')]).message_post(body=body,
                                                                             subject=None,
                                                                             message_type='comment',
                                                                             subtype='mail.mt_comment',
                                                                             parent_id=False,
                                                                             attachments=None,
                                                                             content_subtype='html',
                                                                             **{
                                                                                 'author_id': 3})


def result_time_val(date_time):
    if len(date_time) > 1:
        result_date = date_time[0]
        for time_one in range(1, len(date_time)):
            if datetime.strptime(date_time[time_one].split(' ')[0],
                                 '%Y-%m-%d') > datetime.strptime(
                    result_date.split(' ')[0], '%Y-%m-%d'):
                result_date = date_time[time_one]
        return result_date
    elif len(date_time) == 1:
        return date_time[0]
    return ''


class ResPartner(models.Model):
    """"""

    _inherit = 'res.partner'

    priority = fields.Selection(AVAILABLE_PRIORITIES, string=u'客户星级', index=True,
                                default=AVAILABLE_PRIORITIES[0][0])

    detailed_address = fields.Char(string=u'地址', compute='_street_name')

    source = fields.Char(string=u'来源')
    continent = fields.Many2one('crm.continent', string=u'所属大洲')
    express_sample_record = fields.Char(string=u'快递账号')
    interested_in_product = fields.Many2many('product.template',
                                             'res_interested_in_product_template_ref',
                                             string=u'感兴趣产品')

    product_series_ids = fields.Many2many('crm.product.series',
                                          'res_product_series_product_template_ref',
                                          string=u'感兴趣系列')

    communication_identifier = fields.Char(string=u'其他沟通方式')
    qq = fields.Char(string=u'QQ')

    skype = fields.Char(string=u'Skype')
    whatsapp = fields.Char(string=u'WhatsApp')
    wechat = fields.Char(string=u'微信')

    crm_source_id = fields.Many2one('crm.lead.source', string=u'来源')

    source_id = fields.Many2one('res.partner.source')

    customer_status = fields.Many2one('message.order.status', string=u'客户状态')
    is_order = fields.Boolean(string=u'订单记录', readonly=True, compute='_compute_is_order',
                              store=True)

    user_id = fields.Many2one('res.users', string='Salesperson',
                              default=lambda self: self.env.user,
                              help='The internal user that is in charge of communicating with this contact if any.')
    team_id = fields.Many2one('crm.team', string='Sales Team', oldname='section_id',
                              default=lambda self: self.env[
                                  'crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid))

    order_partner_question_count = fields.Integer(
        compute='_compute_order_partner_question', string=u'客户问题汇总')

    partner_img_count = fields.Integer(compute='_compute_order_partner_question',
                                       string=u'客户照片')

    public_partners = fields.Selection(
        [('public', u'公海'), ('buffer', u'缓冲区'), ('private', u'私有')], string=u'公海',
        default='private')

    old_user_id = fields.Char(string=u'前销售员')

    customer_code = fields.Char(string=u'客户简码')
    customer_alias = fields.Char(string=u'客户简称')

    _sql_constraints = [
        ('customer_code', 'unique (customer_code)', u'客户简码不能重复.'),
        ('customer_alias', 'unique (customer_code)', u'客户简称不能重复.'),
    ]

    crm_partner_id = fields.Many2one('crm.res.partner', string='related partner')

    crm_is_partner = fields.Boolean(related='crm_partner_id.crm_is_partner',
                                    string=u'是否线索客户')

    im_tool = fields.Char(related='crm_partner_id.im_tool', string=u'即时通讯工具')

    customer_scale = fields.Selection(
        [('1', u'1-10人'), ('2', u'10-49人'), ('3', u'50-100人'), ('4', u'100-500人'),
         ('5', u'500人以上')],
        related='crm_partner_id.customer_scale', string=u'规模')

    customer_store_number = fields.Integer(related='crm_partner_id.customer_store_number',
                                           string=u'门店数量')

    customer_store_product_type = fields.Char(
        related='crm_partner_id.customer_store_product_type', string=u'门店主营产品类型')

    customer_user_group = fields.Char(related='crm_partner_id.customer_user_group',
                                      string=u'用户群体')

    customer_social_platform = fields.Char(
        related='crm_partner_id.customer_social_platform', string=u'社交平台')

    customer_birthday = fields.Date(related='crm_partner_id.customer_birthday',
                                    string=u'生日')

    customer_sex = fields.Selection([('man', u'男'), ('woman', u'女')],
                                    related='crm_partner_id.customer_sex',
                                    string=u'性别')

    customer_image = fields.Binary(u"照片",
                                   help="This field holds the image used as photo for the employee, limited to 1024x1024px.")

    customer_country_id = fields.Many2many('res.country', string=u'国家')  # 市场
    customer_continent = fields.Many2many('crm.continent', string=u'大洲')  # 市场
    customer_is_world = fields.Boolean(related='crm_partner_id.customer_is_world',
                                       string=u'世界')  # 市场

    # customer_write_date = fields.Datetime(related='crm_partner_id.customer_write_date', string=u'最近操所时间')

    customer_write_date = fields.Datetime(string=u'最近操所时间',
                                          compute="_compute_customer_write_date",
                                          store=True)

    customer_follow_up_date = fields.Date(
        related='crm_partner_id.customer_follow_up_date', string=u'最近跟进时间')

    crm_is_partner_temporary = fields.Boolean(
        related='crm_partner_id.crm_is_partner_temporary', string=u'是否是客户')

    @api.multi
    def _compute_customer_write_date(self):
        for partner in self:
            partner.customer_write_date = partner.write_date

    def _compute_order_partner_question(self):
        for partner in self:
            count = 0
            for sale_order in partner.sale_order_ids:
                for sale_order_my in sale_order.message_ids:
                    if sale_order_my.sale_order_type == 'question':
                        count += 1

            for partner_count in partner.message_ids:
                if partner_count.sale_order_type == 'partner_question':
                    count += 1
            partner.order_partner_question_count = count
            partner.partner_img_count = len(partner.img_ids)

    @api.multi
    def _compute_is_order(self):
        for line in self:
            if line.sale_order_count > 0:
                line.is_order = True

    def fomate_name_vals(self, strip_str):
        name_val = strip_str.replace('.', '').strip()
        is_true = True
        while is_true:
            if name_val.find('  ') != -1:
                name_val = name_val.replace('  ', ' ')
            else:
                is_true = False
        return name_val

    def select_company_new(self, vals, type):
        # if type == 'email':
        #     return True
        strip_str = vals.get(type)
        if self._name == 'crm.lead' and type == 'email':
            type = 'email_from'
        if strip_str != (self[type] if self else ''):
            if strip_str:
                if type == 'name':
                    result_zh = re.findall(ur'[\u4e00-\u9fa5]', strip_str.decode('utf-8'))
                    result_us = re.findall(r'[a-zA-Z0-9]', strip_str)
                    result_zh = ''.join(result_zh)
                    result_us = lower(''.join(result_us))

                    if result_zh and result_us:
                        res_zh = self.env['res.partner'].search(
                            [('name', 'ilike', result_zh), ('customer', '=', True),
                             ('is_company', '=', True)])
                        if self:
                            res_zh = res_zh - self
                        if res_zh:
                            for res_zh_one in res_zh:
                                partner_us = re.findall(r'[a-zA-Z0-9]', res_zh_one.name)
                                partner_us = lower(''.join(partner_us))
                                if partner_us == result_us:
                                    return True
                    elif result_zh:
                        res_zh = self.env['res.partner'].search(
                            [('name', '=', result_zh), ('customer', '=', True),
                             ('is_company', '=', True)])
                        if res_zh:
                            return True
                    elif result_us:
                        res_us = self.env['res.partner'].search(
                            [('name', 'ilike', self.fomate_name_vals(strip_str)),
                             ('customer', '=', True),
                             ('is_company', '=', True)])
                        if self:
                            res_us = res_us - self
                        if res_us:
                            for res_us_one in res_us:
                                partner_us = re.findall(r'[a-zA-Z0-9]', res_us_one.name)
                                partner_us = lower(''.join(partner_us))
                                if partner_us == result_us:
                                    return True
                else:
                    result = self.env['res.partner'].search(
                        [(type, '=', strip_str.strip()), ('customer', '=', True),
                         ('is_company', '=', True)])
                    return result

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = self.fomate_name_vals(vals.get('name'))

        if not (vals.get('company_type') == 'person' or (not vals.get('company_type'))):
            if vals.get('customer'):
                if self.select_company_new(vals, 'name'):
                    raise UserError(u'此名称' + vals.get('name') + u'已绑定公司，请确认')
                if self.select_company_new(vals, 'email'):
                    raise UserError(u'此邮件' + vals.get('email') + u'已绑定公司，请更换')
                # if not vals.get('mutual_rule_id'):
                #     raise UserError(u'请选择客户适用公海规则')

                if vals.get('user_id'):
                    vals['public_partners'] = 'private'
                    vals['old_user_id'] = vals.get('user_id')
                else:
                    vals['public_partners'] = 'public'

                    # if vals.get('mutual_customer_id'):
                    #     # mutual_rule_id
                    #     vals['mutual_rule_id'] = vals.get('mutual_customer_id')

                # 是客户 创建外部表

                crm_res_one = self.env['crm.res.partner'].create({})

                vals['crm_partner_id'] = crm_res_one.id

        res = super(ResPartner, self).create(vals)
        # if (not (res.company_type == 'person')) and res.customer:
        #     lead_vals = {
        #
        #         'name': "默认商机-" + str(res.name),
        #         'partner_id': res.id,
        #         'planned_revenue': 0.0,
        #         'priority': res.priority,
        #         'type': 'opportunity',
        #     }
        #
        #     self.env['crm.lead'].create(lead_vals)

        return res

    @api.multi
    def write(self, vals):
        if len(self) > 1:
            return super(ResPartner, self).write(vals)

        if vals.get('name'):
            vals['name'] = self.fomate_name_vals(vals.get('name'))

        if vals.get('customer'):
            crm_res_one = self.env['crm.res.partner'].create({})
            vals['crm_partner_id'] = crm_res_one.id

        if not (self['company_type'] == 'company' and vals.get(
                'company_type') == 'person'):
            if self['is_company'] or vals.get('is_company'):
                for item_type in ['name', 'email']:
                    if self.select_company_new(vals, item_type):
                        item_type_name = item_type
                        if item_type == 'name':
                            item_type_name = '名称 '
                        elif item_type == 'email':
                            item_type_name = '邮件 '
                        raise UserError(
                            u'此' + item_type_name + vals.get(item_type) + u'已绑定公司，请确认')

        if self['company_type'] == 'person' and vals.get('company_type') == 'company':
            for item_type in ['name', 'email']:
                if not vals.get(item_type):
                    if self.select_company_new({item_type: self[item_type]}, item_type):
                        raise UserError(
                            u'此' + item_type + vals.get(item_type) + u'已绑定公司，请更换')

        if 'user_id' in vals:
            if vals.get('user_id'):
                vals['public_partners'] = 'private'
                vals['old_user_id'] = vals.get('user_id')
                # if vals.get('user_id') == int(self.old_user_id):
                #     raise UserError(u'此用户不允许被领取')
                # else:
                #     vals['public_partners'] = 'private'
                #     vals['old_user_id'] = vals.get('user_id')

                if self.child_ids:
                    for child in self.child_ids:
                        child.user_id = vals.get('user_id')

            else:
                vals['public_partners'] = 'public'

        if 'mutual_rule_id' not in vals:
            vals['customer_write_date'] = datetime.now()

        if 'crm_is_partner_temporary' in vals:
            vals['is_order'] = vals.get('crm_is_partner_temporary')
            if vals.get('crm_is_partner_temporary'):
                vals['crm_is_partner'] = False

        return super(ResPartner, self).write(vals)

    @api.depends('street', 'country_id', 'zip', 'state_id', 'city', 'street', 'street2')
    def _street_name(self):
        for record in self:
            record.detailed_address = ''
            asd = (str(record.country_id.name) if type(
                record.country_id.name) == bool else (
                record.country_id.name).encode("utf-8")) + (
                      str(record.zip) if type(record.zip) == bool else (
                      record.zip).encode("utf-8")) + (
                      str(record.state_id.name) if type(
                          record.state_id.name) == bool else (
                          record.state_id.name).encode(
                          "utf-8")) + (
                      str(record.city) if type(record.city) == bool else (
                      record.city).encode("utf-8")) + (
                      str(record.street) if type(record.street) == bool else (
                      record.street).encode("utf-8")) + (
                      str(record.street2) if type(record.street2) == bool else (
                      record.street2).encode("utf-8"))

            record.detailed_address = asd.replace("False", "")

    remark_count = fields.Integer(u"备注", compute='_compute_remark_count')
    mutual_rule_id = fields.Many2one('crm.mutual.customer', string=u'公海规则')

    @api.multi
    def _compute_remark_count(self):
        activity_data = self.env['crm.remark.record'].read_group(
            [('partner_id', 'in', self.ids)], ['partner_id'],
            ['partner_id'])
        mapped_data = {act['partner_id'][0]: act['partner_id_count'] for act in
                       activity_data}
        for partner in self:
            partner.remark_count = mapped_data.get(partner.id, 0)

    @api.multi
    def crm_public_partner(self):
        mutual_rule_list = self.env['crm.mutual.customer'].search([])
        for mutual_rule in mutual_rule_list:

            abort_time = mutual_rule.effective_time  # 截止时间
            abort_time_date = datetime.strptime(abort_time.split(' ')[0], '%Y-%m-%d')

            overdue_time = mutual_rule.description  # 过期时间
            overdue_time_date = int(overdue_time)

            now_time = datetime.now()  # 现在时间
            now_time_date = datetime.strptime(str(now_time).split(' ')[0], '%Y-%m-%d')

            for partner_one in mutual_rule.customer_ids:

                finally_order_time = partner_one.sale_order_ids[0].create_date if len(
                    partner_one.sale_order_ids) > 0 else partner_one.create_date  # 最后下单时间
                finally_message_time = partner_one.message_ids[0].write_date if len(
                    partner_one.message_ids) > 0 else partner_one.create_date  # 最后跟进时间

                # no_contact_time = finally_message_time  # 未联系时间 差值 difference
                # 原来只能一个参照物判断
                # if mutual_rule.reference_type == 'Order':
                #     no_contact_time = finally_order_time
                # elif mutual_rule.reference_type == 'Follow':
                #     no_contact_time = finally_message_time
                # if not no_contact_time:
                #     no_contact_time = partner_one.create_date

                # 判断多选开始
                temp_date_list = []

                for category_one in mutual_rule.category_id:
                    if category_one.name == 'Order':
                        temp_date_list.append(finally_order_time)
                    elif category_one.name == 'Follow':
                        temp_date_list.append(finally_message_time)
                    elif category_one.name == 'Mail':
                        temp_date_list.append(partner_one.create_date)

                no_contact_time = result_time_val(temp_date_list)

                # 判断多选结束

                if not no_contact_time:
                    no_contact_time = partner_one.create_date

                no_contact_time_difference = datetime.strptime(
                    no_contact_time.split(' ')[0], '%Y-%m-%d')
                no_contact_time_date = now_time_date - no_contact_time_difference

                # 判断开始

                interval_time = abort_time_date - now_time_date  # 》0 还没有到截止时间   《0 已经过了截止时间
                if interval_time.days == 0:
                    # '刚好是截止时间'
                    if no_contact_time_date.days > overdue_time_date:
                        # '设置为公海 取消销售员绑定'
                        partner_one.write({'public_partners': 'public'})
                        partner_one.write({'user_id': ''})
                        action_crm_channel(self, u'客户' + partner_one.name + u'掉入公海')
                    # '取消公海规则'
                    partner_one.write({'mutual_rule_id': ''})
                else:
                    if interval_time.days > 0:
                        if no_contact_time_date.days > overdue_time_date:
                            # '设置为警告用户'
                            partner_one.write({'public_partners': 'buffer'})
                            action_crm_channel(self, u'客户' + partner_one.name + u'进入警告期')
                    if interval_time.days < 0:
                        if (no_contact_time_date.days - abs(
                                interval_time.days)) > overdue_time_date:
                            # '设置为公海 取消销售员绑定'
                            partner_one.write({'public_partners': 'public'})
                            partner_one.write({'user_id': ''})
                            action_crm_channel(self, u'客户' + partner_one.name + u'掉入公海')
                        # '取消规则'
                        partner_one.write({'mutual_rule_id': ''})

    @api.multi
    def init_public_partner_crm(self):
        domain = [('customer', '=', True), ('is_company', '=', True)]
        partner_list = self.env['res.partner'].search(domain)
        for partner_one in partner_list:
            if partner_one.user_id:
                partner_one.write(
                    {'public_partners': 'private', 'old_user_id': partner_one.user_id.id})
            else:
                partner_one.write({'public_partners': 'public'})

    img_ids = fields.One2many('ir.attachment', 'partner_img_id')

    @api.multi
    def action_view_partner_img(self):
        action = self.env.ref('base.action_attachment').read()[0]
        action['domain'] = [('partner_img_id', 'in', self.ids)]
        # action['domain'] = [('res_id', 'in', self.ids)]
        return action

    @api.multi
    def action_tree_list_view_res(self):
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
            'model_lead_partner': 'res.partner',
        }

    @api.onchange('customer')
    def on_change_customer(self):
        if self.customer:
            self.supplier = False
        else:
            self.supplier = True

    @api.onchange('supplier')
    def on_change_supplier(self):
        if self.supplier:
            self.customer = False
        else:
            self.customer = True


class CrmRemarkRecord(models.Model):
    """
    在客户界面显示一个右侧 按钮 =客户评论
    """
    _name = 'crm.remark.record'

    subject = fields.Char(u'主题')
    partner_id = fields.Many2one('res.partner', u'客户')
    detail = fields.Text(string=u'详细')
    real_time = fields.Date(string=u'日期', default=fields.Date.context_today)
    product_visit_record = fields.Many2many('product.template', string=u'拜访记录')


class CrmLeadSource(models.Model):
    _name = 'crm.lead.source'

    name = fields.Char(u'来源')
    detail = fields.Text(string=u'详细')


class CrmProductSeries(models.Model):
    _name = 'crm.product.series'

    name = fields.Char(u'名称')
    detail = fields.Text(string=u'描述')
    crm_Parent_id = fields.Many2one('crm.product.series', string=u'上级')
    crm_product_type = fields.Selection(
        [('brand', u'品牌'), ('series', u'系列'), ('version', u'型号')], string=u'类型')
    crm_Parent_ontomany_ids = fields.One2many('crm.product.series', 'crm_Parent_id',
                                              string=u'下级列表')


class ChannelCrm(models.Model):
    _inherit = 'mail.channel'

    # @api.model
    # def create(self, vals):
    #     print vals
    #     return super(ChannelCrm, self).create(vals)

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False,
                     attachments=None, content_subtype='html', **kwargs):
        # print kwargs.get('author_id')
        if (not kwargs.get('project')) and self.channel_type == 'chat':
            body = '【 聊天 】' + body

        return super(ChannelCrm, self).message_post(body, subject, message_type, subtype,
                                                    parent_id, attachments,
                                                    content_subtype, **kwargs)


class CrmIrAttachment(models.Model):
    _inherit = 'ir.attachment'

    partner_img_id = fields.Many2one('res.partner', string=u'照片客户')

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if not (vals.get('res_model') or vals.get('res_id')):
            if self.env.context.get('active_model') == 'res.partner':
                vals['partner_img_id'] = self.env.context.get('active_ids')[
                    0] if self.env.context.get(
                    'active_ids')  else ''

        return super(CrmIrAttachment, self).create(vals)


class CrmModelLead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    mutual_customer_id = fields.Many2one('crm.mutual.customer', string=u'设置公海规则')

    @api.multi
    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        self.ensure_one()
        values = {
            'team_id': self.team_id.id,
        }

        if self.partner_id:
            values['partner_id'] = self.partner_id.id

        if self.name == 'merge':
            leads = self.opportunity_ids.merge_opportunity()
            if leads.type == "lead":
                values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
                self.with_context(active_ids=leads.ids)._convert_opportunity(values)
            elif not self._context.get('no_force_assignation') or not leads.user_id:
                values['user_id'] = self.user_id.id
                leads.write(values)
        else:
            leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))
            leads.write({'mutual_rule_id': self.mutual_customer_id.id})
            values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
            self._convert_opportunity(values)
            for lead in leads:
                if lead.partner_id and lead.partner_id.user_id != lead.user_id:
                    self.env['res.partner'].browse(lead.partner_id.id).write(
                        {'user_id': lead.user_id.id})

        return leads[0].redirect_opportunity_view()


class CrmResPartner(models.Model):
    _name = 'crm.res.partner'

    crm_my_partner = fields.One2many('res.partner', 'crm_partner_id', u'客户')

    crm_is_partner = fields.Boolean(u'线索客户', default=False)

    im_tool = fields.Char(string=u'即时通讯工具')

    customer_scale = fields.Selection(
        [('1', u'1-10人'), ('2', u'10-49人'), ('3', u'50-100人'), ('4', u'100-500人'),
         ('5', u'500人以上')], string=u'规模')

    customer_store_number = fields.Integer(string=u'门店数量')

    customer_store_product_type = fields.Char(string=u'门店主营产品类型')

    customer_user_group = fields.Char(string=u'用户群体')

    customer_social_platform = fields.Char(string=u'社交平台')

    customer_birthday = fields.Date(string=u'生日')

    customer_sex = fields.Selection([('man', u'男'), ('woman', u'女')], string=u'性别')

    customer_is_world = fields.Boolean(string=u'世界')  # 市场

    crm_is_partner_temporary = fields.Boolean(string=u'是否是客户')

    customer_follow_up_date = fields.Date(string=u'最近跟进时间')


    # @api.model
    # def _default_crm_write_date(self):
    #     return datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
