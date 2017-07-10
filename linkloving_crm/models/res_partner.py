# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
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
    result = my_self.env['res.partner'].search(
        [(type, '=', vals[type].strip()), ('customer', '=', True), ('is_company', '=', True)])
    return result


class ResPartner(models.Model):
    """"""

    _inherit = 'res.partner'

    priority = fields.Selection(AVAILABLE_PRIORITIES, string=u'客户星级', index=True)

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

    @api.multi
    def _compute_is_order(self):
        for line in self:
            if line.sale_order_count > 0:
                line.is_order = True

    @api.model
    def create(self, vals):
        if 'is_company' in vals and 'company_type' in vals:
            if vals['is_company'] == True and vals['company_type'] == 'company':
                if 'name' in vals:
                    if select_company(self, vals, 'name'):
                        raise UserError(u'此名称已绑定公司，请确认')

                if 'email' in vals:
                    if select_company(self, vals, 'email'):
                        raise UserError(u'此Email已绑定公司，请更换')

        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'is_company' in self and 'company_type' in self:
            if self['is_company'] == True and self['company_type'] == 'company':
                if 'name' in vals:
                    if select_company(self, vals, 'name'):
                        raise UserError(u'此名称已绑定公司，请确认')

                if 'email' in vals:
                    if select_company(self, vals, 'email'):
                        raise UserError(u'此Email已绑定公司，请更换')
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

    @api.multi
    def _compute_remark_count(self):
        activity_data = self.env['crm.remark.record'].read_group([('partner_id', 'in', self.ids)], ['partner_id'],
                                                                 ['partner_id'])
        mapped_data = {act['partner_id'][0]: act['partner_id_count'] for act in activity_data}
        for partner in self:
            partner.remark_count = mapped_data.get(partner.id, 0)


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
