# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from datetime import date, time, datetime, timedelta
from odoo import fields, api, models
from odoo.exceptions import UserError

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
    if strip_str:
        result = my_self.env['res.partner'].search(
            [(type, '=', strip_str.strip()), ('customer', '=', True), ('is_company', '=', True)])
        return result


def action_crm_channel(my_self, body):
    my_self.env['mail.channel'].message_post(body=body, subject=None, message_type='comment',
                                             subtype='mail.mt_comment', parent_id=False, attachments=None,
                                             content_subtype='html', **{'author_id': 3})


class ResPartner(models.Model):
    """"""

    _inherit = 'res.partner'

    priority = fields.Selection(AVAILABLE_PRIORITIES, string=u'客户星级', index=True, default=AVAILABLE_PRIORITIES[0][0])

    detailed_address = fields.Char(string=u'地址', compute='_street_name')

    source = fields.Char(string=u'来源')
    continent = fields.Many2one('crm.continent', string=u'所属大洲')
    express_sample_record = fields.Char(string=u'快递账号')
    interested_in_product = fields.Many2many('product.template', 'res_interested_in_product_template_ref',
                                             string=u'感兴趣产品')

    product_series_ids = fields.Many2many('crm.product.series', 'res_product_series_product_template_ref',
                                          string=u'感兴趣系列')

    communication_identifier = fields.Char(string=u'其他沟通方式')
    qq = fields.Char(string=u'QQ')

    skype = fields.Char(string=u'Skype')
    whatsapp = fields.Char(string=u'WhatsApp')
    wechat = fields.Char(string=u'微信')

    crm_source_id = fields.Many2one('crm.lead.source', string=u'来源')

    customer_status = fields.Many2one('message.order.status', string=u'客户状态')
    is_order = fields.Boolean(string=u'订单记录', readonly=True, compute='_compute_is_order', store=True)

    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user,
                              help='The internal user that is in charge of communicating with this contact if any.')
    team_id = fields.Many2one('crm.team', string='Sales Team', oldname='section_id',
                              default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid))

    order_partner_question_count = fields.Integer(compute='_compute_order_partner_question', string=u'客户问题汇总')

    public_partners = fields.Selection([('public', '公海'), ('buffer', '缓冲区'), ('private', '私有')], string=u'公海')

    old_user_id = fields.Char(string=u'前销售员')

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

    @api.multi
    def _compute_is_order(self):
        for line in self:
            if line.sale_order_count > 0:
                line.is_order = True

    @api.model
    def create(self, vals):
        if not (vals.get('company_type') == 'person'):
            if vals.get('is_company'):
                if select_company(self, vals, 'name'):
                    raise UserError(u'此名称' + vals.get('name') + u'已绑定公司，请确认')
                if select_company(self, vals, 'email'):
                    raise UserError(u'此邮件' + vals.get('email') + u'已绑定公司，请更换')

                if vals.get('user_id'):
                    vals['public_partners'] = 'private'
                    vals['old_user_id'] = vals.get('user_id')

        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) > 1: return super(ResPartner, self).write(vals)
        if not (self['company_type'] == 'company' and vals.get('company_type') == 'person'):
            if self['is_company'] or vals.get('is_company'):
                for item_type in ['name', 'email']:
                    if select_company(self, vals, item_type):
                        raise UserError(u'此' + item_type + vals.get(item_type) + u'已绑定公司，请确认')

        if self['company_type'] == 'person' and vals.get('company_type') == 'company':
            for item_type in ['name', 'email']:
                if not vals.get(item_type):
                    if select_company(self, {item_type: self[item_type]}, item_type):
                        raise UserError(u'此' + item_type + vals.get(item_type) + u'已绑定公司，请更换')

        if 'user_id' in vals:
            if vals.get('user_id'):
                vals['public_partners'] = 'private'
                vals['old_user_id'] = vals.get('user_id')
                # if vals.get('user_id') == int(self.old_user_id):
                #     raise UserError(u'此用户不允许被领取')
                # else:
                #     vals['public_partners'] = 'private'
                #     vals['old_user_id'] = vals.get('user_id')
            else:
                vals['public_partners'] = 'public'

        return super(ResPartner, self).write(vals)

    @api.depends('street', 'country_id', 'zip', 'state_id', 'city', 'street', 'street2')
    def _street_name(self):
        for record in self:
            record.detailed_address = ''
            asd = (str(record.country_id.name) if type(record.country_id.name) == bool else (
                record.country_id.name).encode("utf-8")) + (
                      str(record.zip) if type(record.zip) == bool else (record.zip).encode("utf-8")) + (
                      str(record.state_id.name) if type(record.state_id.name) == bool else (
                          record.state_id.name).encode(
                          "utf-8")) + (
                      str(record.city) if type(record.city) == bool else (record.city).encode("utf-8")) + (
                      str(record.street) if type(record.street) == bool else (record.street).encode("utf-8")) + (
                      str(record.street2) if type(record.street2) == bool else (record.street2).encode("utf-8"))

            record.detailed_address = asd.replace("False", "")

    remark_count = fields.Integer(u"备注", compute='_compute_remark_count')
    mutual_rule_id = fields.Many2one('crm.mutual.customer', string=u'公海规则')

    @api.multi
    def _compute_remark_count(self):
        activity_data = self.env['crm.remark.record'].read_group([('partner_id', 'in', self.ids)], ['partner_id'],
                                                                 ['partner_id'])
        mapped_data = {act['partner_id'][0]: act['partner_id_count'] for act in activity_data}
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
                    partner_one.sale_order_ids) > 0 else ''  # 最后下单时间
                finally_message_time = partner_one.message_ids[0].write_date if len(
                    partner_one.message_ids) > 0 else ''  # 最后跟进时间

                no_contact_time = finally_message_time  # 未联系时间 差值 difference
                if mutual_rule.reference_type == 'Order':
                    no_contact_time = finally_order_time
                elif mutual_rule.reference_type == 'Follow':
                    no_contact_time = finally_message_time
                if not no_contact_time:
                    no_contact_time = partner_one.create_date
                no_contact_time_difference = datetime.strptime(no_contact_time.split(' ')[0], '%Y-%m-%d')
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
                        if (no_contact_time_date.days - abs(interval_time.days)) > overdue_time_date:
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
                partner_one.write({'public_partners': 'private', 'old_user_id': partner_one.user_id.id})
            else:
                partner_one.write({'public_partners': 'public'})


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


class ChannelCrm(models.Model):
    _inherit = 'mail.channel'

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification', subtype=None, parent_id=False,
                     attachments=None, content_subtype='html', **kwargs):
        print kwargs.get('author_id')
        if len(self) <= 0:
            # self = self.env['mail.channel'].browse(7)
            self = self.env['mail.channel'].search([('name', '=', '公海通知')])
        return super(ChannelCrm, self).message_post(body, subject, message_type, subtype, parent_id, attachments,
                                                    content_subtype, **kwargs)
