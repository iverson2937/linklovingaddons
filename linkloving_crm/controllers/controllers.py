# -*- coding: utf-8 -*-
import json
import urllib
import urllib2

from odoo import http
from odoo.http import request

import functools
import xmlrpclib


class LinklovingCrm(http.Controller):
    @http.route('/linkloving_crm/init_partner/', auth='public')
    def init_partner(self, **kw):
        ssr = http.request.env['res.partner']
        ssr.init_public_partner_crm()

        return "init partner succeed"

    # 初始化客户 判断客户是否有销售员 有 把客户联系人销售员也改为 客户销售员
    @http.route('/linkloving_crm/init_js_partner/', auth='public')
    def init_js_partner(self):
        domain = [('customer', '=', True), ('is_company', '=', True)]
        partner_list = http.request.env['res.partner'].search(domain)
        for partner_one in partner_list:

            if not (partner_one.team_id and partner_one.crm_source_id and partner_one.customer_status and
                        partner_one.comment and partner_one.product_series_ids and partner_one.message_ids):

                # 获取 若态该客户的信息
                # requrl = "http://192.168.88.124:8069/linkloving_app_api/get_one_demo_partner1?name=" + '中国003'
                # requrl = "http://localhost:8069/linkloving_app_api/get_one_demo_partner1?name=" + partner_one.neme
                requrl = "http://erp.robotime.com/linkloving_app_api/get_one_demo_partner1?name=" + partner_one.neme
                # requrl = 'http://erp.robotime.com/linkloving_app_api/get_stock_picking_by_remark?remark=12'

                req = urllib2.Request(url=requrl)
                res_data = urllib2.urlopen(req)
                res = json.loads(res_data.read())['res_data']

                if (not partner_one.crm_source_id) and res.get('crm_source_id'):  # 赋值来源
                    source_id = http.request.env['crm.lead.source'].search([('name', '=', res.get('crm_source_id'))])
                    partner_one.write({'crm_source_id': source_id.id})

                if (not partner_one.source_id) and res.get('source_id'):  # 赋值来源
                    source_data = http.request.env['res.partner.source'].search([('name', '=', res.get('source_id'))])
                    partner_one.write({'source_id': source_data.id})

                if (not partner_one.customer_status) and res.get('customer_status'):  # 赋值客户状态
                    status_id = http.request.env['message.order.status'].search(
                        [('name', '=', res.get('customer_status'))])
                    partner_one.write({'customer_status': status_id.id})

                if (not partner_one.comment) and res.get('comment'):  # 赋值 备注
                    partner_one.write({'comment': res.get('comment')})

                if (not partner_one.product_series_ids) and res.get('product_series_ids'):  # 赋值 感兴趣产品
                    product_series_list = []
                    for product_series_one in res.get('product_series_ids'):
                        product_id = http.request.env['crm.product.series'].search([('name', '=', product_series_one)])
                        product_series_list.append(product_id.id)
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
