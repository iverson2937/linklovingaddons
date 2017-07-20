# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmMutualCustomer(models.Model):
    _name = 'crm.mutual.customer'

    group_name = fields.Char(string=u'分组名称')

    reference_type = fields.Selection([(u'Follow', u'跟进记录'), (u'Mail', u'接收邮件'), (u'Order', u'订单')], string=u'参考类型',
                                      default=u'Follow')

    description = fields.Char(string=u'移入规则')

    effective_time = fields.Date(string=u'生效时间')

    customer_ids = fields.One2many('res.partner', 'mutual_rule_id', u'客户')

    # customer_ids = fields.Many2many('res.partner', 'crm_mutual_customer_in_res_partner_ref', u'客户')
