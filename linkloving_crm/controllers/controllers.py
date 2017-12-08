# -*- coding: utf-8 -*-
import json
import urllib
import urllib2
import logging

from odoo import http
from odoo.http import request

import functools
import xmlrpclib

_logger = logging.getLogger(__name__)


class LinklovingCrm(http.Controller):
    @http.route('/linkloving_crm/init_partner/', auth='public')
    def init_partner(self, **kw):
        ssr = http.request.env['res.partner']
        ssr.init_public_partner_crm()

        return "init partner succeed"

    # 初始化客户 判断客户是否有销售员 有 把客户联系人销售员也改为 客户销售员
    @http.route('/linkloving_crm/init_js_partner/', auth='public')
    def init_js_partner(self, **kw):

        domain = [('customer', '=', True), ('is_company', '=', True), ('team_id', '=', kw.get('team'))]

        if kw.get('website') == 'true':
            domain.append(('website', 'in', (False, '')))
        elif kw.get('website') == 'false':
            domain.append(('website', 'not in', (False, '')))

        partner_list = http.request.env['res.partner'].search(domain)

        for partner_one in partner_list:

            if not (partner_one.team_id and partner_one.crm_source_id and partner_one.customer_status and
                        partner_one.comment and partner_one.product_series_ids and partner_one.message_ids):

                # 获取 若态该客户的信息
                # requrl = "http://localhost:8069/linkloving_app_api/get_one_demo_partner1?name=" + "4Kidz Inc"
                # requrl = "http://localhost:8069/linkloving_app_api/get_one_demo_partner1"
                requrl = "http://erp.robotime.com/linkloving_app_api/get_one_demo_partner1"

                r = urllib2.Request(url=requrl)
                r.add_data(urllib.urlencode({'name': partner_one.name}))

                print str(partner_one.name) + '*********name********'
                _logger.warning(str(partner_one.name) + '*********name********')
                res_data = urllib2.urlopen(r)  # post method

                # req = urllib2.Request(url=requrl)
                # res_data = urllib2.urlopen(req)
                res = json.loads(res_data.read())['res_data']

                print str(res) + '********* 返回********'
                _logger.warning(str(res) + '********* 返回********')

                if (not partner_one.crm_source_id) and res.get('crm_source_id'):  # 赋值来源
                    source_id = http.request.env['crm.lead.source'].search(
                        [('name', '=', res.get('crm_source_id'))])
                    if source_id:
                        if len(source_id.ids) > 1:
                            source_id = source_id[0]
                    partner_one.write({'crm_source_id': source_id.id})

                if (not partner_one.source_id) and res.get('source_id'):  # 赋值渠道
                    source_data = http.request.env['res.partner.source'].search(
                        [('name', '=', res.get('source_id'))])
                    if source_data:
                        if len(source_data.ids) > 1:
                            source_data = source_data[0]
                    partner_one.write({'source_id': source_data.id})

                if (not partner_one.customer_status) and res.get('customer_status'):  # 赋值客户状态
                    status_id = http.request.env['message.order.status'].search(
                        [('name', '=', res.get('customer_status'))])
                    if status_id:
                        if len(status_id.ids) > 1:
                            status_id = status_id[0]
                    partner_one.write({'customer_status': status_id.id})

                if (not partner_one.comment) and res.get('comment'):  # 赋值 备注
                    partner_one.write({'comment': res.get('comment')})

                if (not partner_one.product_series_ids) and res.get('product_series_ids'):  # 赋值 感兴趣产品
                    product_series_list = []
                    for product_series_one in res.get('product_series_ids'):
                        product_id = http.request.env['crm.product.series'].search(
                            [('name', '=', product_series_one)])
                        if product_id:
                            if len(product_id.ids) > 1:
                                product_id = product_id[0]
                            product_series_list.append(product_id.id)
                    if product_series_list:
                        partner_one.write({'product_series_ids': [(6, 0, product_series_list)]})

                if (not partner_one.message_ids) and res.get('messages_ids'):  # 赋值 跟进记录
                    request.session.authenticate(u'js10', 'peter.wang@robotime.com', '123456')
                    msg_list = []

                    message_s = res.get('messages_ids')
                    message_s.reverse()

                    for msg_data in message_s:
                        label_list = []
                        for label_id in msg_data.get('message_label_ids'):
                            message_label_id = http.request.env['message.label'].search([('name', '=', label_id)])
                            if message_label_id:
                                if len(message_label_id.ids) > 1:
                                    message_label_id = message_label_id[0]
                            label_list.append(message_label_id.id)

                        msg_id = http.request.env['mail.message'].create(
                            {'body': msg_data.get('body'), 'message_label_ids': [(6, 0, label_list)],
                             'res_id': partner_one.id, 'model': 'res.partner'})
                        msg_list.append(msg_id.id)

                    partner_one.write({'messages_ids': msg_list})

        return http.local_redirect('/web')

    # 建立外键关系表  初始化之前的数据
    @http.route('/linkloving_crm/init_ago_partner/', auth='public')
    def init_partner(self, **kw):
        par_list = http.request.env['res.partner'].sudo().search([])
        for par_list_one in par_list:
            if not par_list_one.crm_partner_id:
                ssr = http.request.env['crm.res.partner'].create({})
                par_list_one.write({'crm_partner_id': ssr.id})

        return "init partner succeed"

    @http.route('/linkloving_crm/create_attachment', type='json', auth='public', website=True, csrf=False)
    def create_attachment_index(self, **kw):
        Model_Attachment = request.env['ir.attachment']

        content = kw.get('content')
        file_name = kw.get('file')

        attachment_one = Model_Attachment.create({
            'res_model': u'blog.post',
            'name': file_name,
            'datas': content.split('base64,')[1] if content.split('base64,') else content,
            'datas_fname': file_name,
            'public': True,
        })
        return str(attachment_one.id)
