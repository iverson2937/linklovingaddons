# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, time, datetime, timedelta
from odoo.exceptions import ValidationError, UserError


class VisitPartner(models.Model):
    _name = "visit.partner"

    name = fields.Char(u'表格记录人')
    team = fields.Many2one('crm.team', u'销售团队')
    partner_name = fields.Char(u'客户名称', require=True)
    partner_address = fields.Char(u'客户地址', require=True)
    partner_channel = fields.Char(u'客户渠道', require=True)

    visit_date_begin = fields.Datetime(string=u'开始时间', require=True)
    visit_date_end = fields.Datetime(string=u'结束时间', require=True)

    visit_name = fields.Char(u'拜访对象', require=True)
    partner_phone = fields.Char(u'电话', require=True)
    partner_contact_way = fields.Char(u'QQ/Email', require=True)
    partner_state = fields.Char(u'状态', require=True)
    visit_target = fields.Char(u'拜访目标', require=True)
    partner_img_ids = fields.Many2many('ir.attachment', string=u'客户名片照片', require=True)

    content_description = fields.Text(u'沟通内容', require=True)
    summary = fields.Text(u'总结', require=True)

    visit_images = fields.One2many(comodel_name="visit.partner.image", inverse_name="visit_partner_id",
                                  string="客户名片照片",
                                  required=False, )

    @api.model
    def create(self, vals):
        begin_time_date = datetime.strptime(str(vals.get('visit_date_begin')), '%Y-%m-%d %H:%M:%S')
        end_time_date = datetime.strptime(str(vals.get('visit_date_end')), '%Y-%m-%d %H:%M:%S')
        if begin_time_date >= end_time_date:
            raise ValidationError(u'结束时间不能小于开始时间')
        return super(VisitPartner, self).create(vals)

class linkloving_visit_image(models.Model):
    _name = 'visit.partner.image'

    visit_image = fields.Binary(u"客户名片照片")

    visit_partner_id = fields.Many2one("visit.partner", ondelete='cascade')