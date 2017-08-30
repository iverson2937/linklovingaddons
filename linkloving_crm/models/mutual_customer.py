# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmMutualCustomer(models.Model):
    _name = 'crm.mutual.customer'

    name = fields.Char(string=u'分组名称')

    reference_type = fields.Selection([(u'Follow', u'跟进记录'), (u'Mail', u'接收邮件'), (u'Order', u'订单')], string=u'参考类型',
                                      default=u'Follow')

    category_id = fields.Many2many('crm.reference.type', string=u'参照物')

    description = fields.Char(string=u'移入规则')

    effective_time = fields.Date(string=u'生效时间')

    customer_ids = fields.One2many('res.partner', 'mutual_rule_id', u'客户')

    # customer_ids = fields.Many2many('res.partner', 'crm_mutual_customer_in_res_partner_ref', u'客户')

    @api.multi
    def action_apply_all_partner(self):
        for mutual in self:
            domain = [('customer', '=', True), ('is_company', '=', True)]
            partner_list = self.env['res.partner'].search(domain)

            for partner_one in partner_list:
                if partner_one.user_id and (not partner_one.mutual_rule_id):
                    partner_one.write({'mutual_rule_id': mutual.id})

                    # 取消应用于全部
                    # for partner_one in partner_list:
                    #     if partner_one.user_id:
                    #         partner_one.write({'mutual_rule_id': ''})


class CrmReferenceType(models.Model):
    _name = 'crm.reference.type'

    # type_name = fields.Char(u'类型')
    name = fields.Selection([(u'Follow', u'跟进记录'), (u'Mail', u'接收邮件'), (u'Order', u'订单')], string=u'参考类型',
                            default=u'Follow')
    describe_name = fields.Text(string=u'描述')
