# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class LinklovingAutoSmtp(http.Controller):
    # email 退订
    @http.route('/linkloving_app_api/unsubscribe_success', auth='public')
    def unsubscribe_success(self, **kw):
        message_data = '你好！退订成功'
        print kw.get('email')

        if request.context.get('lang') != 'zh_CN':
            message_data = 'Unsubscribe success!'

        Model = request.env['email.send.statistics'].sudo()

        try:
            subscribe_list = Model.search([('email', 'ilike', kw.get('email')), ('request_type', '=', 'subscribe')])
            if not subscribe_list:
                Model.create({
                    'email': kw.get('email'),
                    'name': 'subscribe',
                    'request_type': 'subscribe',
                    'is_subscribe': True,
                })
        except Exception, e:
            print e
        finally:
            return message_data

    # 记录已读
    @http.route('/linkloving_app_api/load_email', auth='public')
    def load_email(self, **kw):
        message_data = '记录已读'

        print kw.get('email'), kw.get('title')

        Model = request.env['email.send.statistics'].sudo()
        try:
            subscribe_load_list = Model.search([('email', '=', kw.get('email')), ('name', '=', str(kw.get('title')))])
            if not subscribe_load_list:
                Model.create({
                    'email': kw.get('email'),
                    'name': kw.get('title'),
                    'request_type': 'read',
                })
        except Exception, e:
            print e
        finally:
            return message_data

            # return message_data
