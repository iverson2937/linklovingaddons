# -*- coding: utf-8 -*-
import base64
import copy
import json
import logging
from urllib2 import URLError

import time

import operator

import datetime

import jpush
import pytz
from pip import download

import odoo
import odoo.modules.registry
from odoo import fields
from odoo.osv import expression
from odoo.tools import float_compare, SUPERUSER_ID, werkzeug, os, safe_eval
from odoo.tools.translate import _
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

app_key = "f2ae889d6e4c3400fef49696"
master_secret = "e1d3af4d5ab66d45f6255c18"
_jpush = jpush.JPush(app_key, master_secret)
push = _jpush.create_push()
_jpush.set_logging("DEBUG")

need_sound = "a.caf"
apns_production = False


class JPushExtend:
    @classmethod
    def send_notification_push(cls, platform=jpush.all_, audience=None, notification=None, body='', message=None,
                               apns_production=False):
        push.audience = audience
        ios = jpush.ios(alert={"title": notification,
                               "body": body,
                               }, sound=need_sound)
        android = jpush.android(alert=body, title=notification)
        push.notification = jpush.notification(ios=ios, android=android)
        push.options = {"apns_production": apns_production, }
        push.platform = platform
        try:
            response = push.send()
        except jpush.common.Unauthorized:
            print ("Unauthorized")
        except jpush.common.APIConnectionException:
            print ("APIConnectionException")
        except jpush.common.JPushFailure:
            print ("JPushFailure")
        except:
            print ("Exception")


STATUS_CODE_OK = 1
STATUS_CODE_ERROR = -1


# 返回的json 封装
class JsonResponse(object):
    @classmethod
    def send_response(cls, res_code, res_msg='', res_data=None, jsonRequest=True):
        data_dic = {'res_code': res_code,
                    'res_msg': res_msg, }
        if res_data:
            data_dic['res_data'] = res_data
        if jsonRequest:
            return data_dic
        return json.dumps(data_dic)


class LinklovingAppApi(http.Controller):
    # 获取数据库列表
    @http.route('/linkloving_app_api/is_inner_ip', type='http', auth='none', cors='*')
    def is_inner_ip(self, **kw):
        remote_addr = request.httprequest.environ.get('HTTP_X_REAL_IP')
        if remote_addr in ['112.80.45.130', '221.224.85.74', '49.75.219.17', '221.225.245.181']:
            return JsonResponse.send_response(STATUS_CODE_OK, res_data={'origin_ip': remote_addr},
                                              jsonRequest=False)
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={'origin_ip': remote_addr},
                                              jsonRequest=False)

    @classmethod
    def CURRENT_USER(cls, force_admin=False):
        uid = request.jsonrequest.get("uid")
        if uid:
            return uid
        if not force_admin:
            return request.context.get("uid")
        else:
            return SUPERUSER_ID

    odoo10 = None

    # 获取数据库列表
    @http.route('/linkloving_app_api/get_db_list', type='http', auth='none', cors='*')
    def get_db_list(self, **kw):
        print 'sss'
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=http.db_list(), jsonRequest=False)

    # 换头像。
    @http.route('/linkloving_app_api/change_img', type='json', auth="none", csrf=False, cors='*')
    def change_img(self, **kw):
        uid = request.jsonrequest.get("uid")
        user = request.env['res.users'].sudo().browse(
            uid)  # LinklovingAppApi.get_model_by_id(uid, request, 'res.users')
        user.partner_id.image = request.jsonrequest['img']
        cur_user = request.env['res.users'].browse(uid)
        values = {}
        values['user_ava'] = LinklovingAppApi.get_img_url(cur_user.id, "res.users", "image_medium")
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', uid)])
        user.write({
            "image": request.jsonrequest['img'],
            "image_medium": request.jsonrequest['img'],
            "image_small": request.jsonrequest['img']
        })
        employee.write({
            "image": request.jsonrequest['img'],
            "image_medium": request.jsonrequest['img'],
            "image_small": request.jsonrequest['img']
        })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=values)

    # 登录
    @http.route('/linkloving_app_api/login', type='json', auth="none", csrf=False, cors='*')
    def login(self, **kw):
        request.session.db = request.jsonrequest["db"]
        request.params["db"] = request.jsonrequest["db"]

        request.params['login_success'] = False
        values = request.params.copy()
        app_version = request.jsonrequest.get("app_version")
        if not app_version:
            raise UserError(u"请更新新版OA,否则无法使用")

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db, request.jsonrequest['login'],
                                               request.jsonrequest['password'])
            cur_partner = request.env['res.partner'].sudo().search([('sub_company', '=', 'sub')])
            values['is_company_main'] = False
            if cur_partner:
                if len(cur_partner) > 0:
                    values['is_company_main'] = True
            if uid is not False:
                request.params['login_success'] = True
                cur_user = request.env['res.users'].browse(request.uid)

                employee_all_child = request.env['hr.employee'].get_employee_child(cur_user.employee_ids)
                values['employee_all_child'] = employee_all_child.ids
                values['name'] = cur_user.name
                values['user_id'] = request.uid
                # get group ids
                user = request.env['res.users'].sudo().browse(
                    uid)  # LinklovingAppApi.get_model_by_id(uid, request, 'res.users')

                values['partner_id'] = user.partner_id.id
                values['company'] = user.company_id.name
                # rate = request.env['mrp.config.settings'].sudo().get_default_allow_produced_qty_rate(
                #     ['allow_produced_qty_rate'])
                # values.update(rate)
                if user.employee_ids:
                    values['barcode'] = user.employee_ids[0].barcode
                    values['phone'] = user.employee_ids[0].mobile_phone
                    values['department'] = user.employee_ids[0].department_id.name
                    values['job'] = user.employee_ids[0].job_id.name
                    values['bank_number'] = user.employee_ids[0].bank_account_id.acc_number
                    values['bank_name'] = user.employee_ids[0].bank_account_id.bank_name

                if user.sale_team_id:
                    values['team'] = {
                        'team_id': user.sale_team_id.id,
                        'team_name': user.sale_team_id.name or '',
                    }
                group_names = request.env['ir.model.data'].sudo().search_read([('res_id', 'in', user.groups_id.ids),
                                                                               ('model', '=', 'res.groups')],
                                                                              fields=['name'])
                # 转换中英文标志位
                if user.lang == "zh_CN":
                    values['lang'] = "zh-Hans"
                elif user.lang == "en_US":
                    values['lang'] = "en"
                else:
                    values['lang'] = "zh-Hans"

                values['groups'] = group_names
                values['user_ava'] = LinklovingAppApi.get_img_url(cur_user.id, "res.users", "image_medium")
                values['login_success'] = True
                return JsonResponse.send_response(STATUS_CODE_OK, res_data=values)
            else:
                request.uid = old_uid
                values['error'] = _("Wrong login/password")

        else:
            values['error'] = _("Wrong Request Method")
        return JsonResponse.send_response(STATUS_CODE_ERROR, res_data=values)

    @classmethod
    def get_img_url(cls, id, model, field):
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s&time=%s' % (
            request.httprequest.host_url, str(id), model, field, str(time.mktime(datetime.datetime.now().timetuple())))
        if not url:
            return ''
        return url

    # 获取菜单列表
    @http.route('/linkloving_app_api/get_menu_list', type='http', auth="none", csrf=False)
    def get_menu_list(self, **kw):
        if request.session.uid:
            request.uid = request.session.uid
        # context = LinklovingAppApi.loadMenus()
        menu_data = LinklovingAppApi.loadMenus().get('children')
        if menu_data:
            menu_data = [{'id': 268,
                          'name': "test",
                          "parent_id": False,
                          'sequence': 1,
                          "web_icon": 0,
                          "xml_name": "mrp.menu_mrp_production_action",
                          "children": []
                          }]
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=menu_data, jsonRequest=False)

    @classmethod
    def get_app_menu_icon_img_url(cls, id, field):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s&time=%s' % (
            request.httprequest.host_url, str(id), 'ir.ui.menu', field,
            str(time.mktime(datetime.datetime.now().timetuple())))
        if not url:
            return ''
        return url

    @http.route('/linkloving_app_api/get_rework_ing_production', type='json', auth='none', csrf=False)
    def get_rework_ing_production(self):
        partner_id = request.jsonrequest.get('partner_id')
        mrp_production = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER())
        domain = []
        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))
        domain.append(('state', '=', 'progress'))
        domain.append(('feedback_on_rework', '!=', None))

        production_rework = mrp_production.search(domain,
                                                  offset=request.jsonrequest['offset'],
                                                  limit=request.jsonrequest['limit'],
                                                  order='date_planned_start desc'
                                                  )

        data = []
        for production in production_rework:
            # dict = {
            #     'order_id': production.id,
            #     'display_name': production.display_name,
            #     'product_name': production.product_id.display_name,
            #     'date_planned_start': production.date_planned_start,
            #     'state': production.state,
            #     'product_qty': production.product_qty,
            #     'in_charge_name': production.in_charge_id.name,
            #     'origin': production.origin,
            #     'process_id': {
            #         'process_id': production.process_id.id,
            #         'name': production.process_id.name,
            #     },
            #     'production_line_id': {
            #         'production_line_id': production.production_line_id.id,
            #         'name': production.production_line_id.name
            #     }
            # }

            data.append(self.get_simple_production_json(production))
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    @http.route('/linkloving_app_api/get_production_lines', type='json', auth='none', csrf=False)
    def get_production_lines(self, **kw):
        # request.session.db = request.jsonrequest["db"]
        # request.params["db"] = request.jsonrequest["db"]

        mrp_production = request.env['mrp.production'].sudo()
        partner_id = request.jsonrequest.get('partner_id')
        domain = []
        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))

        if request.jsonrequest.get('state'):
            domain.append(('state', '=', request.jsonrequest['state']))
            if request.jsonrequest.get('state') == 'progress':
                domain.append(('feedback_on_rework', '=', None))

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))
        g = mrp_production.read_group(domain, fields=['production_line_id'], groupby="production_line_id")
        print(g)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=g)

    # 获取生产单列表
    @http.route('/linkloving_app_api/get_mrp_production', type='json', auth='none', csrf=False)
    def get_mrp_production(self, **kw):
        condition = request.jsonrequest.get('condition')
        mrp_production = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER())
        partner_id = request.jsonrequest.get('partner_id')
        domain = []
        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))

        if request.jsonrequest.get('state'):
            domain.append(('state', '=', request.jsonrequest['state']))
            if request.jsonrequest.get('state') == 'progress':
                domain.append(('feedback_on_rework', '=', None))

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if condition and condition[condition.keys()[0]]:
            domain = (condition.keys()[0], 'like', condition[condition.keys()[0]])
        if 'production_line_id' in request.jsonrequest.keys():
            production_line_id = request.jsonrequest.get("production_line_id")
            domain.append(('production_line_id', '=', production_line_id))

        production_all = mrp_production.search(domain,
                                               offset=request.jsonrequest['offset'],
                                               limit=request.jsonrequest['limit'],
                                               order='date_planned_start desc'
                                               )
        data = []
        for production in production_all:
            # dict = {
            #     'order_id': production.id,
            #     'display_name': production.display_name,
            #     'product_name': production.product_id.display_name,
            #     'date_planned_start': production.date_planned_start,
            #     'state': production.state,
            #     'product_qty': production.product_qty,
            #     'qty_produced': production.qty_unpost,
            #     'in_charge_name': production.in_charge_id.name,
            #     'origin': production.origin,
            #     'process_id': {
            #         'process_id': production.process_id.id,
            #         'name': production.process_id.name,
            #     },
            #
            # }
            data.append(self.get_simple_production_json(production))
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    @http.route('/linkloving_app_api/get_process_list', type='json', auth='none', csrf=False)
    def get_process_list(self, **kw):
        process_list = request.env['mrp.process'].sudo(LinklovingAppApi.CURRENT_USER()).search([])
        process_json = []
        for process in process_list:
            process_json.append(LinklovingAppApi.get_process_json(process))

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=process_json)

    @classmethod
    def get_process_json(cls, process):
        return {"process_id": process.id,
                "name": process.name}

    # 根据工序分组. 查看正在生产中的mo
    @http.route('/linkloving_app_api/get_progress_mo_group_by_process', type='json', auth='none', csrf=False)
    def get_progress_mo_group_by_process(self, **kw):
        partner_id = request.jsonrequest.get("partner_id")

        domain_uid = ['|', ('in_charge_id', '=', partner_id), ('create_uid', '=', partner_id)]
        domain = expression.AND([[('state', '=', 'progress')],
                                 domain_uid,
                                 [('feedback_on_rework', '=', None)], ])

        orders_group_by_process = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain
                                                                                                                 ,
                                                                                                                 fields=[
                                                                                                                     "process_id"],
                                                                                                                 groupby=[
                                                                                                                     "process_id"])
        json_list = []
        for group in orders_group_by_process:
            json_list.append({
                "process_id": group["process_id"][0],
                "name": group["process_id"][1],
                "process_count": group["process_id_count"]
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    @classmethod
    def get_today_time_and_tz(cls):
        user = request.env["res.users"].sudo().browse(request.context.get("uid"))
        timez = fields.datetime.now(pytz.timezone(user.tz)).tzinfo._utcoffset
        date_to_show = fields.datetime.utcnow()
        date_to_show += timez
        return date_to_show, timez

    # 单个工序
    @http.route('/linkloving_app_api/get_date_uncomplete_orders', type='json', auth='none', csrf=False)
    def get_date_uncomplete_orders(self, **kw):

        process_id = request.jsonrequest.get("process_id")
        date_to_show, timez = LinklovingAppApi.get_today_time_and_tz()
        one_days_after = datetime.timedelta(days=1)
        today_time = fields.datetime.strptime(fields.datetime.strftime(date_to_show, '%Y-%m-%d'),
                                              '%Y-%m-%d')  # fields.datetime.strftime(date_to_show, '%Y-%m-%d')
        # locations = request.env["stock.location"].sudo().get_semi_finished_location_by_user(request.context.get("uid"))
        # location_cir = request.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
        # location_domain = locations.ids + location_cir
        after_day = today_time + one_days_after
        order_delay = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
            [('date_planned_start', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),

             ('state', 'in', ['waiting_material', 'prepare_material_ing']),

             ('process_id', '=', process_id),
             # ('location_ids', 'in', location_domain)
             ]
            , fields=["date_planned_start"],
            groupby=["date_planned_start"])

        domain = [('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                  ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                  ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                  ('process_id', '=', process_id),
                  # ('location_ids', 'in', location_domain)
                  ]
        today_time = today_time + one_days_after
        after_day = after_day + one_days_after
        domain_tommorrow = [('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                            ('process_id', '=', process_id),
                            # ('location_ids', 'in', location_domain)
                            ]
        today_time = today_time + one_days_after
        after_day = after_day + one_days_after
        domain_after_day = [('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                            ('process_id', '=', process_id),
                            # ('location_ids', 'in', location_domain)
                            ]
        domain_all = [('state', 'in', ['waiting_material', 'prepare_material_ing']),
                      ('process_id', '=', process_id), ]

        order_today = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain,
                                                                                                     fields=[
                                                                                                         "date_planned_start"],
                                                                                                     groupby=[
                                                                                                         "date_planned_start"])
        order_tomorrow = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
            domain_tommorrow,
            fields=["date_planned_start"],
            groupby=["date_planned_start"])
        order_after = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain_after_day,
                                                                                                     fields=[
                                                                                                         "date_planned_start"],
                                                                                                     groupby=[
                                                                                                         "date_planned_start"])

        order_all = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain_all,
                                                                                                   fields=[
                                                                                                       "date_planned_start"],
                                                                                                   groupby=[
                                                                                                       "date_planned_start"])
        list = []

        def get_count_iter(orders):
            count = 0
            for order in orders:
                count += order.get("date_planned_start_count")
            return count

        if order_delay:
            list.append({"state": "delay",
                         "count": get_count_iter(order_delay)})
        if order_today:
            list.append({"state": "today",
                         "count": get_count_iter(order_today)})
        if order_tomorrow:
            list.append({"state": "tomorrow",
                         "count": get_count_iter(order_tomorrow)})
        if order_after:
            list.append({"state": "after",
                         "count": get_count_iter(order_after)})
        if order_all:
            list.append({"state": "all",
                         "count": get_count_iter(order_all)})

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=list)

    # 多个工序 的订单数量
    @http.route('/linkloving_app_api/get_order_count_by_process', type='json', auth='none', csrf=False)
    def get_order_count_by_process(self, **kw):
        process_ids = request.jsonrequest.get("process_ids")
        date_to_show, timez = LinklovingAppApi.get_today_time_and_tz()
        one_days_after = datetime.timedelta(days=1)
        today_time = fields.datetime.strptime(fields.datetime.strftime(date_to_show, '%Y-%m-%d'),
                                              '%Y-%m-%d')  # fields.datetime.strftime(date_to_show, '%Y-%m-%d')
        # locations = request.env["stock.location"].sudo().get_semi_finished_location_by_user(request.context.get("uid"))
        # location_cir = request.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
        # location_domain = locations.ids + location_cir

        after_day = today_time + one_days_after
        after_2_day = after_day + one_days_after
        after_3_day = after_2_day + one_days_after
        process_count_dict = {}

        for process_id in process_ids:
            order_delay = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                [('date_planned_start', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),

                 ('state', 'in', ['waiting_material', 'prepare_material_ing']),

                 ('process_id', '=', process_id),
                 # ('location_ids', 'in', location_domain)
                 ]
                , fields=["date_planned_start"],
                groupby=["date_planned_start"])

            domain = [('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                      ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                      ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                      ('process_id', '=', process_id),
                      # ('location_ids', 'in', location_domain)
                      ]

            domain_tommorrow = [('date_planned_start', '>', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                                ('date_planned_start', '<', (after_2_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                                ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                                ('process_id', '=', process_id),
                                # ('location_ids', 'in', location_domain)
                                ]
            domain_after_day = [('date_planned_start', '>', (after_2_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                                ('date_planned_start', '<', (after_3_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                                ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                                ('process_id', '=', process_id),
                                # ('location_ids', 'in', location_domain)
                                ]

            order_today = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain,
                                                                                                         fields=[
                                                                                                             "date_planned_start"],
                                                                                                         groupby=[
                                                                                                             "date_planned_start"])
            order_tomorrow = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                domain_tommorrow,
                fields=["date_planned_start"],
                groupby=["date_planned_start"])
            order_after = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                domain_after_day,
                fields=["date_planned_start"],
                groupby=["date_planned_start"])

            list = []

            def get_count_iter(orders):
                count = 0
                for order in orders:
                    count += order.get("date_planned_start_count")
                return count

            if order_delay:
                list.append({"state": "delay",
                             "count": get_count_iter(order_delay)})
            if order_today:
                list.append({"state": "today",
                             "count": get_count_iter(order_today)})
            if order_tomorrow:
                list.append({"state": "tomorrow",
                             "count": get_count_iter(order_tomorrow)})
            if order_after:
                list.append({"state": "after",
                             "count": get_count_iter(order_after)})
            process_count_dict[process_id] = list
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=process_count_dict)

    @http.route('/linkloving_app_api/get_recent_production_order', type='json', auth='none', csrf=False)
    def get_recent_production_order(self, **kw):

        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        date_to_show = request.jsonrequest.get("date")
        process_id = request.jsonrequest.get("process_id")
        one_days_after = datetime.timedelta(days=1)
        today_time, timez = LinklovingAppApi.get_today_time_and_tz()
        today_time = fields.datetime.strptime(fields.datetime.strftime(today_time, '%Y-%m-%d'),
                                              '%Y-%m-%d')
        # locations = request.env["stock.location"].sudo().get_semi_finished_location_by_user(request.context.get("uid"))

        if date_to_show not in ["delay", "all"]:
            today_time = fields.datetime.strptime(date_to_show, '%Y-%m-%d')

        one_millisec_before = datetime.timedelta(milliseconds=1)  #
        today_time = today_time - one_millisec_before  # 今天的最后一秒
        after_day = today_time + one_days_after
        # location_cir = request.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
        # location_domain = locations.ids + location_cir
        if not process_id:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "未找到工序id"})

        if date_to_show == "delay":
            domain = [('date_planned_start', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                      ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                      ('process_id', '=', process_id),
                      # ('location_ids', 'in', location_domain)
                      ]
        elif date_to_show == 'all':
            domain = [('state', 'in', ['waiting_material', 'prepare_material_ing']),
                      ('process_id', '=', process_id),
                      # ('location_ids', 'in', location_domain)
                      ]
        else:
            domain = [
                ('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                ('process_id', '=', process_id),
                # ('location_ids', 'in', location_domain)
            ]

        orders_today = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain, limit=limit,
                                                                                                  offset=offset)

        data = []
        for production in orders_today:
            data.append(self.get_simple_production_json(production))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def get_simple_production_json(self, production):
        return {
            'order_id': production.id,
            'display_name': production.display_name,
            'product_name': production.product_id.display_name,
            'date_planned_start': production.date_planned_start,
            'state': production.state,
            'qty_produced': production.qty_unpost,
            'product_qty': production.product_qty,
            'in_charge_name': production.in_charge_id.name,
            'origin': production.origin,
            'process_id': {
                'process_id': production.process_id.id,
                'name': production.process_id.name,
            },
            'production_line_id': {
                'production_line_id': production.production_line_id.id,
                'name': production.production_line_id.name
            },
            'has_produced_product': production.has_produced_product
        }

    def getYesterday(self):
        today = datetime.date.today()
        oneday = datetime.timedelta(seconds=1)
        yesterday = today + oneday
        return str(yesterday)

    # 等待生产的数量
    @http.route('/linkloving_app_api/get_already_picking_orders_count', type='json', auth='none', csrf=False)
    def get_already_picking_orders_count(self, **kw):
        partner_id = request.jsonrequest.get("partner_id")
        date_to_show, timez = LinklovingAppApi.get_today_time_and_tz()
        one_days_after = datetime.timedelta(days=1)
        today_time = fields.datetime.strptime(fields.datetime.strftime(date_to_show, '%Y-%m-%d'),
                                              '%Y-%m-%d')  # fields.datetime.strftime(date_to_show, '%Y-%m-%d')
        # locations = request.env["stock.location"].sudo().get_semi_finished_location_by_user(request.context.get("uid"))
        # location_cir = request.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
        # location_domain = locations.ids + location_cir
        after_day = today_time + one_days_after

        domain_uid = ['|', ('in_charge_id', '=', partner_id), ('create_uid', '=', partner_id)]
        domain_delay = [('picking_material_date', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),

                        ('state', 'in', ['already_picking']),
                        # ('process_id', '=', process_id),
                        # ('location_ids', 'in', location_domain)
                        ]
        domain_delay = expression.AND([domain_delay, domain_uid])
        order_delay = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
            domain_delay
            , fields=["picking_material_date"],
            groupby=["picking_material_date"])

        domain = [('picking_material_date', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                  ('picking_material_date', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                  ('state', 'in', ['already_picking']),
                  # ('process_id', '=', process_id),
                  # ('location_ids', 'in', location_domain)
                  ]
        domain = expression.AND([domain, domain_uid])
        today_time = today_time + one_days_after
        after_day = after_day + one_days_after
        domain_tommorrow = [('picking_material_date', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('picking_material_date', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('state', 'in', ['already_picking']),
                            # ('process_id', '=', process_id),
                            # ('location_ids', 'in', location_domain)
                            ]
        domain_tommorrow = expression.AND([domain_tommorrow, domain_uid])

        today_time = today_time + one_days_after
        after_day = after_day + one_days_after
        domain_after_day = [('picking_material_date', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('picking_material_date', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('state', 'in', ['already_picking']),
                            # ('process_id', '=', process_id),
                            # ('location_ids', 'in', location_domain)
                            ]
        domain_after_day = expression.AND([domain_after_day, domain_uid])

        order_today = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain, fields=[
            "picking_material_date"],
                                                                                                     groupby=[
                                                                                                         "picking_material_date"])
        order_tomorrow = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
            domain_tommorrow,
            fields=["picking_material_date"],
            groupby=["picking_material_date"])
        order_after = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain_after_day,
                                                                                                     fields=[
                                                                                                         "picking_material_date"],
                                                                                                     groupby=[
                                                                                                         "picking_material_date"])

        list = []

        def get_count_iter(orders):
            count = 0
            for order in orders:
                count += order.get("picking_material_date_count")
            return count

        if order_delay:
            list.append({"state": "delay",
                         "count": get_count_iter(order_delay)})
        if order_today:
            list.append({"state": "today",
                         "count": get_count_iter(order_today)})
        if order_tomorrow:
            list.append({"state": "tomorrow",
                         "count": get_count_iter(order_tomorrow)})
        if order_after:
            list.append({"state": "after",
                         "count": get_count_iter(order_after)})
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=list)

    @http.route('/linkloving_app_api/get_recent_alredy_picking_order', type='json', auth='none', csrf=False)
    def get_recent_alredy_picking_order(self, **kw):
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        date_to_show = request.jsonrequest.get("date")
        partner_id = request.jsonrequest.get('partner_id')
        one_days_after = datetime.timedelta(days=1)
        today_time, timez = LinklovingAppApi.get_today_time_and_tz()
        today_time = fields.datetime.strptime(fields.datetime.strftime(today_time, '%Y-%m-%d'),
                                              '%Y-%m-%d')

        domain_uid = ['|', ('in_charge_id', '=', partner_id), ('create_uid', '=', partner_id)]

        if date_to_show != "delay":
            today_time = fields.datetime.strptime(date_to_show, '%Y-%m-%d')

        one_millisec_before = datetime.timedelta(milliseconds=1)  #
        today_time = today_time - one_millisec_before  # 今天的最后一秒
        after_day = today_time + one_days_after
        user = request.env["res.users"].sudo().browse(request.context.get("uid"))

        timez = fields.datetime.now(pytz.timezone(user.tz)).tzinfo._utcoffset

        if date_to_show == "delay":
            domain = [('picking_material_date', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                      ('state', 'in', ['already_picking']),
                      ]
        else:
            domain = [
                ('picking_material_date', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                ('picking_material_date', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                ('state', 'in', ['already_picking']),
            ]
        domain = expression.AND([domain, domain_uid])
        orders_today = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain, limit=limit,
                                                                                                  offset=offset)

        data = []
        for production in orders_today:
            data.append(self.get_simple_production_json(production))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取生产单详细内容
    @http.route('/linkloving_app_api/get_order_detail', type='json', auth='none', csrf=False)
    def get_order_detail(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 确认订单
    @http.route('/linkloving_app_api/confirm_order', type='json', auth='none', csrf=False)
    def confirm_order(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        order_type = request.jsonrequest.get('order_type')
        mrp_production_model = request.env['mrp.production']
        mrp_production = mrp_production_model.sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', order_id)])[0]
        mrp_production.write({'state': 'waiting_material',
                              'production_order_type': order_type})
        qty_wizard = request.env['change.production.qty'].sudo().create({
            'mo_id': mrp_production.id,
            'product_qty': mrp_production.product_qty,
        })
        qty_wizard.change_prod_qty()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 根据生产单号，查询工人列表
    @http.route('/linkloving_app_api/find_worker_lines', type='json', auth='none', csrf=False)
    def find_worker_lines(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if production:
            lines = production.worker_line_ids
            dict_lines = []
            for line in lines:
                dict_lines.append(self.get_worker_line_dict(line))
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=dict_lines)
        else:
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data={})

    @http.route('/linkloving_app_api/find_free_workers', type='json', auth='none', csrf=False)
    def find_free_workers(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        free_workers = request.env['hr.employee'].sudo().search(
            [('now_mo_id', 'not in', [order_id]), ('is_worker', '=', True)])
        free_worker_json = []
        for worker in free_workers:
            free_worker_json.append(self.get_worker_dict(worker))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=free_worker_json)

    # 添加工人
    @http.route('/linkloving_app_api/add_worker', type='json', auth='none', csrf=False)
    def add_worker(self, **kw):
        barcode = request.jsonrequest.get('barcode')
        order_id = request.jsonrequest.get('order_id')
        is_add = request.jsonrequest.get('is_add')
        worker_ids = request.jsonrequest.get('worker_ids')
        domain = []
        if worker_ids and len(worker_ids):
            domain.append(('id', 'in', worker_ids))
        if barcode:
            domain.append(('barcode', '=', barcode))
        if worker_ids is None and barcode is None:
            domain.append(('id', '=', 0))

        domain.append(('is_worker', '=', True))
        workers = request.env['hr.employee'].sudo().search(domain)
        if not is_add:  # 如果只是查询工人信息 - 则直接返回员工信息
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=self.get_worker_dict(workers[0]))
        if not workers:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": _("The operator not found")})
        else:
            for worker in workers:
                if worker.now_mo_id and worker.now_mo_id.id != order_id:  # 是否正在另一条产线，就退出那一条
                    working_now = request.env['worker.line'].sudo(LinklovingAppApi.CURRENT_USER()).search(
                        [('worker_id', '=', worker.id),
                         ('production_id', '=', worker.now_mo_id.id)])
                    working_now.change_worker_state('outline')
                    worker.now_mo_id = None
                elif worker.now_mo_id.id == order_id:  # 防止重复添加
                    continue
                userd_working_line = request.env['worker.line'].sudo(LinklovingAppApi.CURRENT_USER()).search(
                    [('worker_id', '=', worker.id), ('production_id', '=', order_id)])
                if userd_working_line:  # 如果曾在这条贡献干过就继续
                    userd_working_line.change_worker_state('online')
                else:
                    worker_line = request.env['worker.line'].sudo(LinklovingAppApi.CURRENT_USER()).create({
                        'production_id': order_id,
                        'worker_id': worker.id
                    })
                    worker.now_mo_id = order_id
                    worker_line.create_time_line()

            worker_lines = []
            for line in LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production').worker_line_ids:
                worker_lines.append(self.get_worker_line_dict(line))
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=worker_lines)

    def get_worker_dict(self, worker):
        data = {
            'name': worker.name,
            'worker_id': worker.id,
            'image': self.get_worker_url(worker.id),
            'barcode': worker.barcode,
            'job_name': worker.job_id.name or '',
            'card_num': worker.card_num or '',
        }
        return data

    def get_worker_url(self, worker_id, ):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
            request.httprequest.host_url, str(worker_id), 'hr.employee', 'image')
        if not url:
            return ''
        return url

    def get_worker_line_dict(self, obj):
        worker_time_line_ids_list = []
        for time_l in obj.worker_time_line_ids:
            worker_time_line_ids_list.append({
                'worker_id': time_l.worker_id.id,
                'start_time': time_l.start_time,
                'end_time': time_l.end_time,
                'state': time_l.state,
            })
        return {
            'worker_id': obj.id,
            'worker': {
                'worker_id': obj.worker_id.id,
                'name': obj.worker_id.name
            },
            'worker_time_line_ids': worker_time_line_ids_list,
            'line_state': obj.line_state,
            'unit_price': obj.unit_price,
            'xishu': obj.xishu,
            'amount_of_money': obj.amount_of_money,

        }

    # 修改工人状态
    @http.route('/linkloving_app_api/change_worker_state', type='json', auth='none', csrf=False)
    def change_worker_state(self, **kw):
        is_all_pending = request.jsonrequest.get('is_all_pending')
        order_id = request.jsonrequest.get('order_id')
        worker_line_id = request.jsonrequest.get('worker_line_id')
        new_state = request.jsonrequest.get('state')
        production_order = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if is_all_pending:  # 如果是批量暂停
            worker_lines = production_order.worker_line_ids
            # worker_lines = request.env['worker.line'].sudo().search([('id', 'in', worker_line_id)])
            worker_lines.change_worker_state(new_state)
            production_order.is_pending = True
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))
        if not worker_line_id and not is_all_pending:  # 批量恢复
            worker_lines = production_order.worker_line_ids
            # worker_lines = request.env['worker.line'].sudo().search([('id', 'in', worker_line_id)])
            worker_lines.change_worker_state(new_state)

            production_order.is_pending = False
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

        worker_line = request.env['worker.line'].sudo(LinklovingAppApi.CURRENT_USER()).search(
            [('id', '=', worker_line_id)])
        worker_line.change_worker_state(new_state)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.get_worker_line_dict(worker_line))

    # 取消订单
    @http.route('/linkloving_app_api/cancel_order', type='json', auth='none', csrf=False)
    def cancel_order(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        mrp_production_model = request.env['mrp.production']
        mrp_production = mrp_production_model.sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', order_id)])[0]
        mrp_production.action_cancel()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 更新产品数量
    @http.route('/linkloving_app_api/update_produce', type='json', auth='none', csrf=False)
    def update_produce(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        qty = request.jsonrequest.get('product_qty')
        mrp_production_model = request.env['mrp.production']
        mrp_production = mrp_production_model.sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', order_id)])[0]

        qty_wizard = request.env['change.production.qty'].sudo().create({
            'mo_id': mrp_production.id,
            'product_qty': qty,
        })
        qty_wizard.change_prod_qty()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 准备备料
    @http.route('/linkloving_app_api/prepare_material_ing', type='json', auth='none', csrf=False)
    def prepare_material_ing(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        mrp_production_model = request.env['mrp.production']
        mrp_production = mrp_production_model.sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', order_id)])[0]
        mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write({'state': 'prepare_material_ing'})

        JPushExtend.send_notification_push(audience=jpush.audience(
            jpush.tag(LinklovingAppApi.get_jpush_tags("produce"))
        ), notification=mrp_production.product_id.name,
            body=_("Qty:%d,Already start picking！") % (mrp_production.product_qty))

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 保存物料数据
    @http.route('/linkloving_app_api/saving_material_data', type='json', auth='none', csrf=False)
    def saving_material_data(self, **kw):
        # order_id = request.jsonrequest.get('order_id') #get paramter
        stock_moves = request.jsonrequest.get('stock_moves')  # get paramter
        for stock_move in stock_moves:
            sim_move_obj = request.env["sim.stock.move"].sudo(LinklovingAppApi.CURRENT_USER()).browse(
                stock_move["stock_move_lines_id"])
            sim_move_obj.quantity_ready = stock_move['quantity_ready']
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})

    # 备料完成
    @http.route('/linkloving_app_api/finish_prepare_material', type='json', auth='none', csrf=False)
    def finish_prepare_material(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = \
            request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', order_id)])[0]

        stock_moves = request.jsonrequest.get('stock_moves')  # get paramter
        # _logger.warning(u"charlie_0712_log:finish_prepare_material, mo:%s,moves:%s", mrp_production.name, stock_moves)
        # print(u"charlie_0712_log:finish_prepare_material, mo:%s,moves:%s" % (mrp_production.name, stock_moves))
        stock_move_lines = request.env["sim.stock.move"].sudo(LinklovingAppApi.CURRENT_USER())
        try:
            for move in stock_moves:
                sim_stock_move = LinklovingAppApi.get_model_by_id(move['stock_move_lines_id'], request,
                                                                  'sim.stock.move')
                stock_move_lines += sim_stock_move
                if not sim_stock_move.stock_moves:
                    continue

                if move['quantity_ready'] > 0:
                    sim_stock_move.is_prepare_finished = True
                else:
                    continue
                rounding = sim_stock_move.stock_moves[0].product_uom.rounding
                if float_compare(move['quantity_ready'], sim_stock_move.stock_moves[0].product_uom_qty,
                                 precision_rounding=rounding) > 0:
                    # _logger.warning(u"charlie_0712_log_1:move_qty:%s,move_id:%d,uom_qty:%s",
                    #                 str(move['quantity_ready']),
                    #                 sim_stock_move.stock_moves[0].id,
                    #                 str(sim_stock_move.stock_moves[0].product_uom_qty))

                    qty_split = sim_stock_move.stock_moves[0].product_uom._compute_quantity(
                        move['quantity_ready'] - sim_stock_move.stock_moves[0].product_uom_qty,
                        sim_stock_move.stock_moves[0].product_id.uom_id)
                    # _logger.warning(u"charlie_0712_log_2:qty_split:%s,", str(qty_split))
                    split_move = sim_stock_move.stock_moves[0].copy(
                        default={'quantity_done': qty_split, 'product_uom_qty': qty_split,
                                 'production_id': sim_stock_move.production_id.id,
                                 'raw_material_production_id': sim_stock_move.raw_material_production_id.id,
                                 'procurement_id': sim_stock_move.procurement_id.id or False,
                                 'is_over_picking': True})
                    # _logger.warning(u"charlie_0712_log_3:split_move_qty:%s,", split_move)
                    sim_stock_move.production_id.move_raw_ids = sim_stock_move.production_id.move_raw_ids + split_move
                    # _logger.warning(u"charlie_0712_log_4:len_move_raw_ids:%d,",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                    split_move.write({'state': 'assigned', })
                    sim_stock_move.stock_moves[0].quantity_done = sim_stock_move.stock_moves[0].product_uom_qty
                    # _logger.warning(u"charlie_0712_log_5:len_move_raw_ids:%d,",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                    split_move.action_done()
                    # _logger.warning(u"charlie_0712_log_6:len_move_raw_ids:%d,",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                    sim_stock_move.stock_moves[0].action_done()
                    # _logger.warning(u"charlie_0712_log_7:len_move_raw_ids:%d,",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                else:
                    # _logger.warning(u"charlie_0712_log_8:move_qty:%s,uom_qty:%s", str(move['quantity_ready']),
                    #                 str(sim_stock_move.stock_moves[0].product_uom_qty))
                    sim_stock_move.stock_moves[0].quantity_done_store = move['quantity_ready']
                    sim_stock_move.stock_moves[0].quantity_done = move['quantity_ready']
                    sim_stock_move.stock_moves[0].action_done()
                    # _logger.warning(u"charlie_0712_log_9:len_move_raw_ids:%d",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                sim_stock_move.quantity_ready = 0  # 清0
            # try:
            #     mrp_production.post_inventory()
            # except UserError, e:.filtered(lambda x: x.product_type != 'semi-finished')
            #     return JsonResponse.send_response(STATUS_CODE_ERROR,
            #                                       res_data={"error":e.name})
            if all(sim_move.is_prepare_finished for sim_move in
                   stock_move_lines.filtered(lambda x: x.product_type != 'semi-finished')):
                mrp_production.write(
                    {'state': 'finish_prepare_material'})

                JPushExtend.send_notification_push(audience=jpush.audience(
                    jpush.tag(LinklovingAppApi.get_jpush_tags("produce"))
                ), notification=mrp_production.product_id.name,
                    body=_("Qty:%d,Finish picking！") % (mrp_production.product_qty))
        except Exception, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": e.name})
        # _logger.warning(u"charlie_0712_log10:finish, mo:%s", LinklovingAppApi.model_convert_to_dict(order_id, request))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 领料登记
    @http.route('/linkloving_app_api/already_picking', type='json', auth='none', csrf=False)
    def already_picking(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        stock_moves = request.jsonrequest.get('stock_moves')  # get paramter

        for move in stock_moves:
            sim_stock_move = LinklovingAppApi.get_model_by_id(move['stock_move_lines_id'], request, 'sim.stock.move')
            if not sim_stock_move.stock_moves:
                continue
            rounding = sim_stock_move.stock_moves[0].product_uom.rounding
            if float_compare(move['quantity_ready'], sim_stock_move.stock_moves[0].product_uom_qty,
                             precision_rounding=rounding) > 0:
                qty_split = sim_stock_move.stock_moves[0].product_uom._compute_quantity(
                    move['quantity_ready'] - sim_stock_move.stock_moves[0].product_uom_qty,
                    sim_stock_move.stock_moves[0].product_id.uom_id)

                split_move = sim_stock_move.stock_moves[0].copy(
                    default={'quantity_done': qty_split, 'product_uom_qty': qty_split,
                             'production_id': sim_stock_move.production_id.id,
                             'raw_material_production_id': sim_stock_move.raw_material_production_id.id,
                             'procurement_id': sim_stock_move.procurement_id.id or False,
                             'is_over_picking': True})
                sim_stock_move.production_id.move_raw_ids = sim_stock_move.production_id.move_raw_ids + split_move
                split_move.write({'state': 'assigned', })
                sim_stock_move.stock_moves[0].quantity_done = sim_stock_move.stock_moves[0].product_uom_qty
                split_move.action_done()
                sim_stock_move.stock_moves[0].action_done()
            else:
                sim_stock_move.stock_moves[0].quantity_done_store = move['quantity_ready']
                sim_stock_move.stock_moves[0].quantity_done = move['quantity_ready']
                sim_stock_move.stock_moves[0].action_done()
            sim_stock_move.quantity_ready = 0  # 清0
        # try:
        #     mrp_production.post_inventory()
        # except UserError, e:
        #     return JsonResponse.send_response(STATUS_CODE_ERROR,
        #                                       res_data={"error":e.name})

        mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write({'state': 'already_picking',
                                                                               'picking_material_date': fields.datetime.now()})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 开始生产
    @http.route('/linkloving_app_api/start_produce', type='json', auth='none', csrf=False)
    def start_produce(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).button_start_produce()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 补领料
    @http.route('/linkloving_app_api/over_picking', type='json', auth='none', csrf=False)
    def over_picking(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')

        stock_moves = request.jsonrequest.get('stock_moves')  # get paramter
        for l in stock_moves:
            move = LinklovingAppApi.get_model_by_id(l['stock_move_lines_id'], request, 'sim.stock.move')
            if not move:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={'error': _("Stock move not found")})
            if l['over_picking_qty'] != 0:  # 如果超领数量不等于0
                moves_to_do = move.stock_moves.filtered(lambda x: x.state not in ('done', 'cancel'))
                if moves_to_do:
                    moves_to_do[0].quantity_done += l['over_picking_qty']
                    moves_to_do[0].action_done()
                else:
                    new_move = move.stock_moves[0].copy(default={'quantity_done': l['over_picking_qty'],
                                                                 'product_uom_qty': l['over_picking_qty'],
                                                                 'production_id': move.production_id.id,
                                                                 'raw_material_production_id': move.raw_material_production_id.id,
                                                                 'procurement_id': move.procurement_id.id or False,
                                                                 'is_over_picking': True})

                    move.production_id.move_raw_ids = move.production_id.move_raw_ids + new_move
                    move.over_picking_qty = 0
                    new_move.write({'state': 'assigned'})
                    new_move.action_done()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 产出
    @http.route('/linkloving_app_api/do_produce', type='json', auth='none', csrf=False)
    def do_produce(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if not mrp_production:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("The MO not found")})
        produce_qty = request.jsonrequest.get('produce_qty')

        try:
            mrp_product_produce = request.env['mrp.product.produce'].with_context({'active_id': order_id})
            # if mrp_production.is_multi_output or mrp_production.is_random_output:
            #     print produce_qty
            #     mrp_production.create_multi_output(produce_qty)
            #     return JsonResponse.send_response(STATUS_CODE_OK,
            #                                       res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

            produce = mrp_product_produce.sudo(LinklovingAppApi.CURRENT_USER()).create({
                'product_qty': produce_qty,
                'production_id': order_id,
                'product_uom_id': mrp_production.product_uom_id.id,
                'product_id': mrp_production.product_id.id,
            })
            produce.do_produce()
        except Exception, e:
            raise UserError(e)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 送往品检
    @http.route('/linkloving_app_api/produce_finish', type='json', auth='none', csrf=False)
    def produce_finish(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')

        if not mrp_production:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("The MO not found")})
        if mrp_production.qty_unpost == 0:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Product qty can not be 0 ")})
        if mrp_production.qty_unpost < mrp_production.product_qty and mrp_production.production_order_type == 'ordering':
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Ordering MO need to produce all the products")})
        else:
            if mrp_production.feedback_on_rework:  # 生产完成, 但是还在返工中 说明此次返工还没产出
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={"error": u"该单据还在返工中,请先产出数量"})
            # 生产完成 结算工时
            mrp_production.produce_finish_data_handle()
            # mrp_production.state = mrp_production.compute_order_state()
            # if not mrp_production.is_secondary_produce:#不是第二次生产,则重新排产
            #     if 'produce_finish_replan_mo' in dir(mrp_production):
            #         mrp_production.produce_finish_replan_mo()
            # else:#第二次生产,不影响排产,记录时间
            #     times = mrp_production.secondary_produce_time_ids.filtered(lambda x: x.end_time is None)
            #     if times:#正常来说只有一个是没设置结束时间的
            #         times[0].end_time = fields.Datetime.now()
            #     else:
            #         raise UserError(u"未找到对应的数据")

            JPushExtend.send_notification_push(audience=jpush.audience(
                jpush.tag(LinklovingAppApi.get_jpush_tags("qc"))
            ),
                notification=mrp_production.product_id.name,
                body=u"数量:%d, %s" % (mrp_production.qty_produced, mrp_production.state))

            mrp_production.worker_line_ids.change_worker_state('outline')

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    @http.route('/linkloving_app_api/review_procure_info', type='json', auth='none', csrf=False)
    def review_procure_info(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        order = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).browse(order_id)
        if order:
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data={"produce_img": LinklovingAppApi.get_img_url(order_id,
                                                                                                    'mrp.production',
                                                                                                    'produce_img'),
                                                        "produce_area_id": {
                                                            "area_id": order.produce_area_id.id,
                                                            "area_name": order.produce_area_id.name
                                                        }})

    # 生产完成,填写成品位置信息
    @http.route('/linkloving_app_api/upload_procure_info', type='json', auth='none', csrf=False)
    def upload_procure_info(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        procure_img = request.jsonrequest.get('procure_img')
        area_name = request.jsonrequest.get('area_name')
        order = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).browse(order_id)
        area = request.env['stock.location.area'].sudo().search(
            [('name', '=', area_name)])
        if not order:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': u"找不到对应的mo单"})
        if not area:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Please choose the right location")})
        order.produce_img = procure_img
        order.produce_area_id = area[0].id
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})

    # 开始品检
    @http.route('/linkloving_app_api/start_quality_inspection', type='json', auth='none', csrf=False)
    def start_quality_inspection(self, **kw):
        feedback_id = request.jsonrequest.get('feedback_id')  # get paramter
        feedback = LinklovingAppApi.get_model_by_id(feedback_id, request, 'mrp.qc.feedback')
        if not feedback_id:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': u"未找到对应的品检单"})
        feedback.sudo(request.context.get("uid") or SUPERUSER_ID).action_start_qc()

        JPushExtend.send_notification_push(audience=jpush.audience(
            jpush.tag(LinklovingAppApi.get_jpush_tags("produce"))
        ), notification=feedback.production_id.product_id.name, body=_("Qty:%d,QC start") % (feedback.qty_produced))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.convert_qc_feedback_to_json(feedback))

    # 品检结果
    @http.route('/linkloving_app_api/inspection_result', type='json', auth='none', csrf=False)
    def inspection_result(self, **kw):

        feedback_id = request.jsonrequest.get('feedback_id')  # get paramter
        result = request.jsonrequest.get('result')

        qc_test_qty = request.jsonrequest.get('qc_test_qty')  # 抽样数量
        qc_fail_qty = request.jsonrequest.get('qc_fail_qty')  # 不良品数量
        qc_note = request.jsonrequest.get('qc_note')  # 批注
        qc_img = request.jsonrequest.get('qc_img')  # 图片
        feedback = LinklovingAppApi.get_model_by_id(feedback_id, request, 'mrp.qc.feedback')
        feedback.write({
            'qc_test_qty': qc_test_qty,
            'qc_fail_qty': qc_fail_qty,
            'qc_note': qc_note,
        })
        for img in qc_img:
            qc_img_id = request.env["qc.feedback.img"].sudo(LinklovingAppApi.CURRENT_USER()).create({
                'feedback_id': feedback.id,
                'qc_img': img,
            })
            feedback.qc_imgs = [(4, qc_img_id.id)]

        if not feedback:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("MO not found")})
        try:
            if result == True:
                feedback.action_qc_success()
            else:
                feedback.action_qc_fail()
        except UserError, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": e.name})

        JPushExtend.send_notification_push(audience=jpush.audience(
            jpush.tag(LinklovingAppApi.get_jpush_tags("produce"))
        ), notification=feedback.production_id.product_id.name, body=_("Qty:%d,QC finish") % (feedback.qty_produced))

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.convert_qc_feedback_to_json(feedback))

    @classmethod
    def get_qc_img_url(cls, worker_id, ):
        # DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        imgs = []
        for img_id in worker_id:
            url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
                request.httprequest.host_url, str(img_id), 'qc.feedback.img', 'qc_img')
            imgs.append(url)
        return imgs

    @http.route('/linkloving_app_api/start_rework', type='json', auth='none', csrf=False)
    def start_rework(self, **kw):
        feedback_id = request.jsonrequest.get('feedback_id')  # get paramter
        feedback = LinklovingAppApi.get_model_by_id(feedback_id, request, 'mrp.qc.feedback')
        try:
            feedback.sudo().action_check_to_rework()
        except UserError, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": e.name})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.convert_qc_feedback_to_json(feedback))

    # 即将弃用
    @http.route('/linkloving_app_api/semi_finished_return_material', type='json', auth='none', csrf=False)
    def semi_finished_return_material(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        stock_move_ids = request.jsonrequest.get('stock_moves')
        is_check = request.jsonrequest.get('is_check')
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if not mrp_production:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("MO not found")})
        return_lines = []
        if all(stock_move.get("return_qty") == 0 for stock_move in stock_move_ids):
            mrp_production.sudo(
                request.context.get("uid") or SUPERUSER_ID).button_mark_done()  # write({'state': 'done'})
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))
        if not is_check:
            for l in stock_move_ids:
                product_id = l['product_tmpl_id']
                obj = request.env['return.material.line'].sudo(LinklovingAppApi.CURRENT_USER()).create({
                    'return_qty': l['return_qty'],
                    'product_id': product_id,
                })
                return_lines.append(obj.id)

            return_material_model = request.env['mrp.return.material']
            returun_material_obj = return_material_model.sudo(LinklovingAppApi.CURRENT_USER()).search(
                [('production_id', '=', order_id),
                 ('state', '=', 'draft')])
            if not returun_material_obj:  # 如果没生成过就生成一遍， 防止出现多条记录
                returun_material_obj = return_material_model.sudo(LinklovingAppApi.CURRENT_USER()).create({
                    'production_id': mrp_production.id,
                })

            else:
                returun_material_obj.production_id = mrp_production.id

            returun_material_obj.return_ids = return_lines
            mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write(
                {'state': 'waiting_warehouse_inspection'})
        else:
            return_material_model = request.env['mrp.return.material']
            returun_material_obj = return_material_model.sudo(LinklovingAppApi.CURRENT_USER()).search(
                [('production_id', '=', order_id),
                 ('state', '=', 'draft')])
            if not returun_material_obj:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={'error': _("Order of return material not found")})
            returun_material_obj.state = 'done'
            # 退料信息 已经确认
            for r in returun_material_obj.return_ids:
                for new_qty_dic in stock_move_ids:
                    if r.product_id.id == new_qty_dic['product_tmpl_id']:
                        r.return_qty = new_qty_dic['return_qty']
                if r.return_qty == 0:
                    continue
                move = request.env['stock.move'].sudo(LinklovingAppApi.CURRENT_USER()).create(
                    returun_material_obj._prepare_move_values(r))
                move.action_done()
            returun_material_obj.return_ids.create_scraps()
            mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).button_mark_done()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 退料
    @http.route('/linkloving_app_api/return_material', type='json', auth='none', csrf=False)
    def return_material(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        stock_move_ids = request.jsonrequest.get('stock_moves')
        is_check = request.jsonrequest.get('is_check')
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        force_cancel = request.jsonrequest.get('force_cancel')
        return_material_model = request.env['mrp.return.material'].sudo(LinklovingAppApi.CURRENT_USER())

        if force_cancel:
            returun_material_obj = return_material_model.get_progress_return_order(order_id=order_id)

        else:
            if all(stock_move.get("return_qty") == 0 for stock_move in stock_move_ids):
                mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).button_mark_done()
                return JsonResponse.send_response(STATUS_CODE_OK,
                                                  res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

            returun_material_obj = return_material_model.get_normal_return_order(order_id=order_id)

        # ---------------------***--------------------
        if not returun_material_obj and not is_check:  # 如果没生成过就生成一遍， 防止出现多条记录
            returun_material_obj = return_material_model.sudo(LinklovingAppApi.CURRENT_USER()).create({
                'production_id': mrp_production.id,
                'return_type': 'progress_return' if force_cancel else 'normal'
            })
        elif not returun_material_obj and is_check:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Order of return material not found")})
        else:
            returun_material_obj.production_id = mrp_production.id

        if not is_check:  # 清点退料
            for l in stock_move_ids:
                obj = request.env['return.material.line'].sudo(LinklovingAppApi.CURRENT_USER()).create({
                    'return_qty': l['return_qty'],
                    'product_id': l['product_tmpl_id'],
                    'return_id': returun_material_obj.id,
                })
        else:  # 仓库检验退料
            for r in returun_material_obj.return_ids:
                for new_qty_dic in stock_move_ids:
                    if r.product_id.id == new_qty_dic['product_tmpl_id']:
                        r.return_qty = new_qty_dic['return_qty']
        # ---------------------***--------------------
        if force_cancel:
            returun_material_obj.do_force_cancel_return()
        else:
            returun_material_obj.with_context({'is_checking': is_check}).do_return()

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 任意状态退料
    @http.route('/linkloving_app_api/return_material_anytime', type='json', auth='none', csrf=False)
    def return_material_anytime(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        stock_move_ids = request.jsonrequest.get('stock_moves')
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if not mrp_production:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("MO not found")})
        if all(stock_move.get("return_qty") == 0 for stock_move in stock_move_ids):
            raise UserError(u"退料数量不能全为0")
        return_material_model = request.env['mrp.return.material']
        returun_material_obj = return_material_model.sudo(LinklovingAppApi.CURRENT_USER()).create({
            'production_id': mrp_production.id,
            'return_type': 'progress_return',
        })
        for l in stock_move_ids:
            obj = request.env['return.material.line'].sudo(LinklovingAppApi.CURRENT_USER()).create({
                'return_qty': l['return_qty'],
                'product_id': l['product_tmpl_id'],
                'return_id': returun_material_obj.id,
            })
        # 直接进行退料
        returun_material_obj.generate_move_and_action_done()

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 获得退料单信息
    @http.route('/linkloving_app_api/get_return_detail', type='json', auth='none', csrf=False)
    def get_return_detail(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        return_material_model = request.env['mrp.return.material'].sudo(LinklovingAppApi.CURRENT_USER())
        state = request.jsonrequest.get("state")
        if state == 'force_cancel':
            return_material_obj = return_material_model.get_progress_return_order(order_id=order_id)
        else:
            return_material_obj = return_material_model.get_normal_return_order(order_id=order_id)

        return_lines = return_material_obj.read()
        if not return_lines:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": u"退料单异常,请在网页端操作"})
        return_lines[0]['product_ids'] = []
        data = []
        for return_line in return_material_obj.return_ids:
            dic = {
                'product_tmpl_id': return_line.product_id.id,
                'product_id': return_line.product_id.display_name,
                'return_qty': return_line.return_qty,
                'product_type': return_line.product_type,
                'weight': return_line.product_id.weight or 0,
            }
            data.append(dic)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=data)

    @http.route('/linkloving_app_api/get_feedback_detail', type='json', auth='none', csrf=False)
    def get_feedback_detail(self, **kw):
        feedback_id = request.jsonrequest.get('feedback_id')
        feedback = request.env["mrp.qc.feedback"].sudo(LinklovingAppApi.CURRENT_USER()).browse(feedback_id)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.convert_qc_feedback_to_json(feedback))

    @http.route('/linkloving_app_api/get_qc_feedback', type='json', auth='none', csrf=False)
    def get_qc_feedback(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        order_id = request.jsonrequest.get('order_id')
        state = request.jsonrequest.get('state')
        if order_id:
            feedbacks = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).browse(
                order_id).qc_feedback_ids
        if state:
            feedbacks = request.env["mrp.qc.feedback"].sudo(LinklovingAppApi.CURRENT_USER()).search(
                [("state", '=', state)],
                limit=limit,
                offset=offset,
                order='production_id desc')
        # if not production_order.qc_feedback_id:
        json_list = []
        for qc_feedback in feedbacks:
            json_list.append(self.convert_qc_feedback_to_json(qc_feedback))

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=json_list)

    def convert_qc_feedback_to_json(self, qc_feedback):
        data = {
            'feedback_id': qc_feedback.id,
            'name': qc_feedback.name,
            'production_id': {
                "order_id": qc_feedback.sudo().production_id.id,
                "display_name": qc_feedback.sudo().production_id.display_name,
                'product_id': {
                    'product_id': qc_feedback.product_id.id,
                    'product_name': qc_feedback.product_id.name,
                    "product_default_code": qc_feedback.product_id.default_code or '',
                    'product_specs': qc_feedback.product_id.product_specs or '',
                    'image_ids': [
                        {'image_url': LinklovingAppApi.get_product_image_url_new(urlBean.id, 'ir.attachment')}
                        for urlBean in qc_feedback.product_id.product_img_ids]
                },
            },
            'state': qc_feedback.state,
            'qty_produced': qc_feedback.qty_produced,
            'qc_test_qty': qc_feedback.qc_test_qty,
            'qc_rate': qc_feedback.qc_rate,
            'qc_fail_qty': qc_feedback.qc_fail_qty,
            'qc_fail_rate': qc_feedback.qc_fail_rate,
            'qc_note': qc_feedback.qc_note or '',
            'qc_img': LinklovingAppApi.get_qc_img_url(qc_feedback.qc_imgs.ids),
        }
        return data

    # 生产完成入库
    @http.route('/linkloving_app_api/produce_done', type='json', auth='none', csrf=False)
    def produce_done(self, **kw):
        feedback_id = request.jsonrequest.get('feedback_id')  # get paramter
        feedback = LinklovingAppApi.get_model_by_id(feedback_id, request, 'mrp.qc.feedback')
        if not feedback:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': u"未找到对应的品检单"})
        try:
            feedback.action_post_inventory()
        except UserError, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": e.name})

        JPushExtend.send_notification_push(audience=jpush.audience(
            jpush.tag(LinklovingAppApi.get_jpush_tags("produce"))
        ),
            notification=feedback.production_id.product_id.name,
            body=_("Qty:%d,Post Inventory Finish") % (feedback.qty_produced))

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.convert_qc_feedback_to_json(feedback))

    # 根据id 和model  返回对应的实例
    @classmethod
    def get_model_by_id(cls, id, request, model):
        model_obj = request.env[model].sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', id)])
        if model_obj:
            return model_obj[0]
        else:
            return None

    # 生产单转换成json
    @classmethod
    def model_convert_to_dict(cls, order_id, request, ):
        mrp_production = request.env['mrp.production'].sudo()
        production = mrp_production.search([('id', '=', order_id)], limit=1)
        done_stock_moves = []
        is_multi_output = is_random_output = False
        if (hasattr(production, 'is_multi_output') and production.is_multi_output) or (
                hasattr(production, 'is_random_output') and production.is_random_output):
            done_stock_moves = request.env['stock.move.finished'].sudo().search_read(
                [('id', 'in', production.stock_move_lines_finished.ids)],
                fields=['product_id',
                        'produce_qty'
                        ])
            is_multi_output = production.is_multi_output
            is_random_output = production.is_random_output

        stock_move = request.env['sim.stock.move'].sudo().search_read(
            [('id', 'in', production.sim_stock_move_lines.ids)],
            fields=['product_id',
                    'over_picking_qty',
                    'qty_available',
                    'quantity_available',
                    'quantity_done',
                    'return_qty',
                    'virtual_available',
                    'quantity_ready',
                    'product_uom_qty',
                    'quantity_available',
                    'suggest_qty',
                    'area_id',
                    'product_type'
                    ])
        # semi_finish = []
        # material = []
        for done_move in done_stock_moves:
            done_move['product_id'] = done_move['product_id'][1]
            done_move['product_tmpl_id'] = done_move['product_id'][0]

        for l in stock_move:
            # dic = LinklovingAppApi.search(request,'product.product',[('id','=',l['product_id'][0])], ['display_name'])
            if l.get("product_id"):
                l['product_tmpl_id'] = l['product_id'][
                    0]
                product = request.env['product.product'].sudo().search([('id', '=', l['product_id'][0])])
                l['weight'] = product.weight
                l['product_id'] = l['product_id'][1]
            if l.get('area_id'):
                l['area_id'] = {
                    'area_id': l.get('area_id')[0] or 0,
                    'area_name': l.get('area_id')[1] or '',
                }
            else:
                l.pop('area_id')
            l['order_id'] = order_id
            # if l.get("product_type") == "semi_finish":#如果是半成品
            #     semi_finish.append(l)
            # else:
            #     material.append(l)

        data = {
            'order_id': production.id,
            'display_name': production.display_name,
            'product_name': production.product_id.display_name,
            'sop_file_url': request.env["product.attachment.info"].get_file_download_url('sop',
                                                                                         request.httprequest.host_url,
                                                                                         production.product_tmpl_id.id),
            'product_id': {
                'product_id': production.product_id.id,
                'product_name': production.product_id.display_name,
                'product_ll_type': production.product_id.product_ll_type or '',
                'product_specs': production.product_id.product_specs,
                'weight': production.product_id.weight,
                'area_id': {
                    'area_id': production.product_id.area_id.id,
                    'area_name': production.product_id.area_id.name,
                }
            },
            'date_planned_start': production.date_planned_start,
            'bom_name': production.bom_id.display_name,
            'state': production.state,
            'product_qty': production.product_qty,
            'production_order_type': production.production_order_type,
            'in_charge_name': production.in_charge_id.name,
            'origin': production.origin,
            'cur_location': None,
            'stock_move_lines': stock_move,
            'done_stock_moves': done_stock_moves,

            'qty_produced': production.qty_unpost,
            'process_id': {
                'process_id': production.process_id.id,
                'name': production.process_id.name,
                'is_rework': production.process_id.is_rework,
                'is_multi_output': is_multi_output,
                'is_random_output': is_random_output
            },
            'prepare_material_area_id': {
                'area_id': production.prepare_material_area_id.id,
                'area_name': production.prepare_material_area_id.name,
            },
            'prepare_material_img': LinklovingAppApi.get_prepare_material_img_url(production.id),
            'is_pending': production.is_pending,
            'feedback_on_rework': {
                'feedback_id': production.feedback_on_rework.id,
                'name': production.feedback_on_rework.name or None,
            },
            'sale_remark': production.sale_remark or '',
            'remark': production.remark or '',
            'is_bom_update': production.is_bom_update,
            'bom_remark': production.bom_id.bom_remark or '',
            'production_line_id': {
                'production_line_id': production.production_line_id.id,
                'name': production.production_line_id.name
            },
            'is_secondary_produce': production.is_secondary_produce,
            # 'factory_remark': production.factory_remark,
        }
        return data

    @classmethod
    def get_prepare_material_img_url(cls, worker_id, ):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
            request.httprequest.host_url, str(worker_id), 'mrp.production', 'prepare_material_img')
        if not url:
            return ''
        return url

    # 盘点接口
    # 根据条件查找产品
    @http.route('/linkloving_app_api/find_product_by_condition', type='json', auth='none', csrf=False)
    def find_product_by_condition(self, **kw):
        condition_dic = request.jsonrequest.get('condition')
        domain = []
        for key in condition_dic.keys():
            if key == 'default_code':
                domain.append((key, '=', condition_dic[key]))
            else:
                domain.append((key, 'in', [condition_dic[key]]))
        sudo_model = request.env['product.product'].sudo(LinklovingAppApi.CURRENT_USER())
        product_s = sudo_model.search(domain)
        if product_s:
            data = {
                'theoretical_qty': product_s.qty_available,
                'product_qty': 0,
                'product': {
                    'product_id': product_s.id,
                    'product_name': product_s.display_name,
                    'image_medium': LinklovingAppApi.get_product_image_url(product_s, model='product.product'),
                    'weight': product_s.weight,
                    'product_spec': product_s.product_specs,
                    'area': {
                        'area_id': product_s.area_id.id,
                        'area_name': product_s.area_id.name,
                    }
                }
            }
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=data)
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Product not found")})

    # 获取盘点单列表
    @http.route('/linkloving_app_api/get_stock_inventory_list', type='json', auth='none', csrf=False)
    def get_stock_inventory_list(self, **kw):
        offset = request.jsonrequest.get('offset')
        limit = request.jsonrequest.get('limit')
        list = request.env['stock.inventory'].sudo(LinklovingAppApi.CURRENT_USER()).search([], order='date desc',
                                                                                           offset=offset, limit=limit)
        stock_inventory_list = []
        print 'start---' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for line in list:
            stock_inventory_list.append(LinklovingAppApi.stock_inventory_model_to_dict(line, is_detail=False))
        print 'end---' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=stock_inventory_list)

    @http.route('/linkloving_app_api/get_stock_inventory_detail', type='json', auth='none', csrf=False)
    def get_stock_inventory_detail(self, **kw):
        inventory_id = request.jsonrequest.get('inventory_id')
        inventory = request.env['stock.inventory'].sudo(LinklovingAppApi.CURRENT_USER()).search(
            [('id', '=', inventory_id)], limit=1)
        if inventory:
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.stock_inventory_model_to_dict(inventory[0],
                                                                                                      is_detail=True))
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Order not found")})

            # stock.location.area 处理部分

    # 获取仓库位置列表
    @http.route('/linkloving_app_api/get_area_list', type='json', auth='none', csrf=False)
    def get_area_list(self, **kw):
        condition = request.jsonrequest.get('condition')
        domain = []
        if condition:
            domain.append(('name', 'ilike', condition))
        areas = request.env['stock.location.area'].sudo().search(domain)
        areas_json = []
        for area in areas:
            areas_json.append(LinklovingAppApi.get_area_json(area))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=areas_json)

    @classmethod
    def get_area_json(cls, area):
        data = {
            "area_id": area.id,
            "area_name": area.name
        }
        return data

    # 所有关于交接信息的处理
    @http.route('/linkloving_app_api/upload_note_info', type='json', auth='none', csrf=False)
    def upload_note_info(self, **kw):
        type = request.jsonrequest.get('type')  # 交接所处的类型，状态
        order_id = request.jsonrequest.get('order_id')  # 生产单号
        img = request.jsonrequest.get('img')
        area_name = request.jsonrequest.get('area_name')
        if type in ['prepare_material_ing', 'already_picking']:
            mrp_order = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
            area = request.env['stock.location.area'].sudo().search(
                [('name', '=', area_name)])
            if not area:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={'error': _("Location error!")})
            mrp_order.prepare_material_area_id = area.id
            mrp_order.prepare_material_img = img
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Wrong status")})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})

    # 创建盘点单
    @http.route('/linkloving_app_api/create_stock_inventory', type='json', auth='none', csrf=False)
    def create_stock_inventory(self, **kw):
        print 'create_stock_inventory1'
        stock_inventory_lines = request.jsonrequest.get('line_ids')
        name = request.jsonrequest.get('name')
        new_lines = []
        try:
            for line in stock_inventory_lines:
                product_obj = LinklovingAppApi.get_model_by_id(line['product']['product_id'], request,
                                                               'product.product')
                line['product_uom_id'] = product_obj.uom_id.id
                product_obj.weight = line['product'].get('weight')
                product_obj.area_id = line['product']['area']['area_id']
                if line['product'].get('image_medium'):
                    try:
                        image_str = line['product'].get('image_medium')
                        print 'image_str:%s' % image_str[0:16]

                        product_obj.product_tmpl_id.image_medium = image_str
                    except Exception, e:
                        print "exception catch %s" % image_str[0:16]
                location_id = request.env.ref('stock.stock_location_stock', raise_if_not_found=False).id

                new_line = {
                    'product_id': product_obj.id,
                    'product_uom_id': product_obj.uom_id.id,
                    'location_id': location_id,
                    'product_qty': line['product_qty'],
                }
                new_lines.append((0, 0, new_line))
        except:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": "数据提交异常"})
        try:
            inventory = request.env['stock.inventory'].sudo(LinklovingAppApi.CURRENT_USER()).create({
                'name': name,
                'filter': 'partial',
                'line_ids': new_lines,
                'state': 'confirm',
                'date': fields.Datetime.now()
            })
            # inventory.action_done()
        except UserError, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": e.name})

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})

    @classmethod
    def stock_inventory_model_to_dict(cls, obj, is_detail):
        line_ids = []
        if is_detail:
            line_ids = request.env['stock.inventory.line'].sudo(LinklovingAppApi.CURRENT_USER()).search_read(
                [('id', 'in', obj.line_ids.ids)], fields=['product_id',
                                                          'product_qty',
                                                          'theoretical_qty',
                                                          ])
            for line in line_ids:
                product_n = request.env['product.product'].sudo(LinklovingAppApi.CURRENT_USER()).browse(
                    line['product_id'][0])
                area = product_n.area_id
                c = {
                    'id': line['product_id'][0],
                    'product_name': line['product_id'][1],
                    'product_spec': product_n.product_specs,
                    'weight': product_n.weight,
                    'image_medium': LinklovingAppApi.get_product_image_url(
                        request.env['product.product'].sudo(LinklovingAppApi.CURRENT_USER()).browse(
                            line['product_id'][0])[0],
                        model='product.product'),
                    'area': {
                        'area_id': area.id,
                        'area_name': area.name
                    }
                }
                line['product'] = c
                if line.get('product_id'):
                    line.pop('product_id')
                    # c['product_id'] = line['product_id'][0] #request.env['product.product'].sudo().search([('id','=',l['product_id'][0])]).id
                    # line['product_name'] = request.env['product.product'].sudo().search([('id','=',line['product_id'][0])]).display_name
        print 'trans start---' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        data = {
            'id': obj.id,
            'date': obj.date,
            'name': obj.display_name,
            'location_name': obj.location_id.name,
            'state': obj.state,
            # 'total_qty' : obj.total_qty,
            'line_ids': line_ids if line_ids else None
        }

        print 'trans end---' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return data

    @classmethod
    def get_product_image_url(cls, product_product, model):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        if model == 'product.template':
            url = '%slinkloving_app_api/get_product_image?product_id=%s&model=%s' % \
                  (request.httprequest.host_url, str(product_product.id), model)
        else:
            url = '%slinkloving_app_api/get_product_image?product_id=%s&model=%s' % \
                  (request.httprequest.host_url, str(product_product.product_tmpl_id.id), model)
        if not url:
            return ''
        return url

    @http.route('/linkloving_app_api/get_product_image', type='http', auth='none', csrf=False)
    def get_product_image(self, **kw):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        product_id = kw.get('product_id')
        status, headers, content = request.registry['ir.http'].binary_content(xmlid=None,
                                                                              model='product.template',
                                                                              id=product_id,
                                                                              field='image_medium',
                                                                              unique=time.strftime(
                                                                                  DEFAULT_SERVER_DATE_FORMAT,
                                                                                  time.localtime()),
                                                                              default_mimetype='image/png',
                                                                              env=request.env(user=SUPERUSER_ID))
        if status == 304:
            return werkzeug.wrappers.Response(status=304, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200 and download:
            return request.not_found()

        if content:
            content = odoo.tools.image_resize_image(base64_source=content, size=(None, None),
                                                    encoding='base64', filetype='PNG')
            # resize force png as filetype
            headers = self.force_contenttype(headers, contenttype='image/png')

        if content:
            image_base64 = base64.b64decode(content)
        else:
            image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
            headers = self.force_contenttype(headers, contenttype='image/png')

        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        return response

    @http.route('/linkloving_app_api/get_worker_image', type='http', auth='none', csrf=False)
    def get_worker_image(self, **kw):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        product_id = kw.get('worker_id')
        model = kw.get('model')
        field = kw.get('field')
        status, headers, content = request.registry['ir.http'].binary_content(xmlid=None, model=model,
                                                                              id=product_id, field=field,
                                                                              unique=time.strftime(
                                                                                  DEFAULT_SERVER_DATE_FORMAT,
                                                                                  time.localtime()),
                                                                              default_mimetype='image/png',
                                                                              env=request.env(user=SUPERUSER_ID))
        if status == 304:
            return werkzeug.wrappers.Response(status=304, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200 and download:
            return request.not_found()

        if content:
            content = odoo.tools.image_resize_image(base64_source=content, size=(None, None),
                                                    encoding='base64', filetype='PNG')
            # resize force png as filetype
            headers = self.force_contenttype(headers, contenttype='image/png')

        if content:
            image_base64 = base64.b64decode(content)
        else:
            image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
            headers = self.force_contenttype(headers, contenttype='image/png')

        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        return response

    @http.route('/payment/order_status', type='http', auth='none', csrf=False, cors='*')
    def order_status(self, **kw):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        product_id = kw.get('pidsss')
        status, headers, content = request.registry['ir.http'].binary_content(xmlid=None, model="ir.attachment",
                                                                              id=product_id,
                                                                              unique=time.strftime(
                                                                                  DEFAULT_SERVER_DATE_FORMAT,
                                                                                  time.localtime()),
                                                                              default_mimetype='image/png',
                                                                              env=request.env(user=SUPERUSER_ID))
        if status == 304:
            return werkzeug.wrappers.Response(status=304, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200 and download:
            return request.not_found()

        if content:
            content = odoo.tools.image_resize_image(base64_source=content, size=(None, None),
                                                    encoding='base64', filetype='PNG')
            # resize force png as filetype
            headers = self.force_contenttype(headers, contenttype='image/png')

        if content:
            image_base64 = base64.b64decode(content)
        else:
            image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
            headers = self.force_contenttype(headers, contenttype='image/png')

        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        return response

    def placeholder(self, image='placeholder.png'):
        addons_path = http.addons_manifest['web']['addons_path']
        return open(os.path.join(addons_path, 'web', 'static', 'src', 'img', image), 'rb').read()

    def force_contenttype(self, headers, contenttype='image/png'):
        dictheaders = dict(headers)
        dictheaders['Content-Type'] = contenttype
        return dictheaders.items()

    # 产品模块
    # 根据条件查找产品
    @http.route('/linkloving_app_api/get_product_list', type='json', auth='none', csrf=False)
    def get_product_list(self, **kw):
        condition_dic = request.jsonrequest.get('condition')
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        product_type = request.jsonrequest.get('product_type')

        def convert_product_type(type):
            if type == 'all':
                return
            elif type == 'purchase':
                return ('purchase_ok', '=', True)
            elif type == 'sale':
                return ('sale_ok', '=', True)
            elif type == 'expensed':
                return ('can_be_expensed', '=', True)
            else:
                return

        domain = []
        if condition_dic:
            for key in condition_dic.keys():
                if condition_dic[key] != '' or not condition_dic[key]:
                    domain.append((key, 'ilike', condition_dic[key]))

        product_json_list = []
        if product_type == 'all':
            list = request.env['product.template'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain, limit=limit,
                                                                                                offset=offset)
            for product in list:
                product_json_list.append(LinklovingAppApi.product_template_obj_to_json(product))


        else:
            domain.append(convert_product_type(product_type))
            list = request.env['product.template'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain, limit=limit,
                                                                                                offset=offset)
            for product in list:
                product_json_list.append(LinklovingAppApi.product_template_obj_to_json(product))

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=product_json_list)

    @http.route('/linkloving_app_api/get_stock_moves_by_product_id', type='json', auth='none', csrf=False)
    def get_stock_moves_by_product_id(self, **kw):
        product_id = request.jsonrequest.get('product_id')
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        if not limit:
            limit = 80
        if not offset:
            offset = 0
        stock_moves = request.env['stock.move'].sudo(LinklovingAppApi.CURRENT_USER()).search(
            [('product_tmpl_id', '=', product_id)], limit=limit, offset=offset)
        stock_move_json_list = []
        for stock_move in stock_moves:
            stock_move_json_list.append(LinklovingAppApi.stock_move_obj_to_json(stock_move))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=stock_move_json_list)

    @classmethod
    def stock_move_obj_to_json(cls, stock_move):
        data = {
            'name': stock_move.name,
            'product_id': {
                'product_name': stock_move.product_tmpl_id.display_name,
                'id': stock_move.product_tmpl_id.id,
            },
            'product_uom_qty': stock_move.product_uom_qty,
            'state': stock_move.state,
            'location': stock_move.location_id.display_name,
            'location_dest': stock_move.location_dest_id.display_name,
            'write_uid': stock_move.write_uid.name if stock_move.write_uid else '',
            'write_date': stock_move.write_date if stock_move.write_date else '',
            'move_order_type': stock_move.move_order_type if stock_move.move_order_type else '',
            'picking_id': stock_move.picking_id.name if stock_move.picking_id else '',
            'quantity_adjusted_qty': stock_move.quantity_adjusted_qty if stock_move.quantity_adjusted_qty else 0,
            'origin': stock_move.origin if stock_move.origin else '',
        }
        return data

    @classmethod
    def product_template_obj_to_json(cls, product_tmpl):
        data = {
            'product_id': product_tmpl.id,
            'product_product_id': product_tmpl.product_variant_id.id,
            'default_code': product_tmpl.default_code,
            'product_name': product_tmpl.name,
            'type': product_tmpl.type,
            'inner_code': product_tmpl.inner_code,
            'inner_spec': product_tmpl.inner_spec,
            'weight': product_tmpl.weight,
            'area_id': {
                'area_name': product_tmpl.area_id.name,
                'area_id': product_tmpl.area_id.id
            },
            'product_spec': product_tmpl.product_specs,
            'image_medium': LinklovingAppApi.get_product_image_url(product_tmpl, model='product.template'),
            'qty_available': product_tmpl.qty_available,
            'virtual_available': product_tmpl.virtual_available,
            'categ_id': product_tmpl.categ_id.name,
            'image_ids': [
                {'image_url': LinklovingAppApi.get_product_image_url_new(urlBean.id, 'ir.attachment')}
                for urlBean in product_tmpl.product_img_ids]
        }
        return data

    @http.route('/linkloving_app_api/get_stock_picking_by_origin', type='json', auth='none', csrf=False)
    def get_stock_picking_by_origin(self, **kw):
        order_name = request.jsonrequest.get("order_name")
        type = request.jsonrequest.get("type")

        if order_name:
            pickings = request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).search(
                [('origin', 'like', order_name),
                 ('picking_type_code', '=', type)])
            json_list = []
            for picking in pickings:
                json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": u"请输入单名"})

    # 产品出入库部分
    @http.route('/linkloving_app_api/get_group_by_list', type='json', auth='none', csrf=False)
    def get_group_by_list(self, **kw):
        groupby = request.jsonrequest.get('groupby')
        model = request.jsonrequest.get('model')
        domain = []
        partner_id = request.jsonrequest.get('partner_id')
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        # if groupby == 'state':
        #     picking_type_id = request.jsonrequest.get('picking_type_id')
        #     domain.append(('picking_type_id', '=', picking_type_id))
        group_list = request.env[model].sudo().read_group(domain, fields=[groupby], groupby=[groupby])
        group_new_list = []
        if groupby == 'picking_type_id':
            for group in group_list:
                group_id = group.get('picking_type_id')[0]
                group_ret = request.env['stock.picking.type'].sudo().search([('id', '=', group_id)], limit=1)
                if group_ret:
                    group_obj = group_ret[0]
                    uid = request.context.get("uid")
                    user = request.env['res.users'].sudo().browse(uid)
                    if group_obj.warehouse_id.company_id.id != user.company_id.id:
                        continue
                temp_domain = []
                temp_domain.append(('picking_type_id', '=', group_id))
                if partner_id:
                    temp_domain.append(('partner_id', 'child_of', partner_id))

                state_group_list = request.env[model].sudo().read_group(temp_domain,
                                                                        fields=['state'],
                                                                        groupby=[
                                                                            'state'])

                new_group = {
                    'picking_type_id': group_id,
                    'picking_type_name': group.get('picking_type_id')[1],
                    'picking_type_code': group_obj.code,
                    'picking_type_id_count': group.get('picking_type_id_count'),
                    'states': state_group_list,
                }
                group_new_list.append(new_group)

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=group_new_list)

    @http.route('/linkloving_app_api/get_outgoing_stock_picking', type='json', auth='none', csrf=False)
    def get_outgoing_stock_picking(self, **kw):
        partner_id = request.jsonrequest.get('partner_id')
        domain = [("state", "in", ("partially_available", "assigned", "confirmed")),
                  ("picking_type_code", "=", "outgoing")]
        domain_complete = [("state", "=", "done"), ("picking_type_code", "=", "outgoing")]

        if partner_id:
            domain = expression.AND([domain, [("partner_id", "child_of", partner_id)]])
            domain_complete = expression.AND([domain_complete, [("partner_id", "child_of", partner_id)]])

        request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).search(
            [("state", "in", ("partially_available", "assigned", "confirmed")),
             ("picking_type_code", "=", "outgoing")])._compute_complete_rate()
        group_list = request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain,
                                                                                                   fields=[
                                                                                                       "complete_rate"],
                                                                                                   groupby=[
                                                                                                       "complete_rate"])

        group_complete = request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain_complete,
                                                                                                       fields=["state"],
                                                                                                       groupby=[
                                                                                                           "state"])
        complete_rate = 99
        complete_rate_count = 0
        new_group = []
        for group in group_list:
            group.pop("__domain")
            if group.get("complete_rate") > 0 and group.get("complete_rate") < 100 or group.get("complete_rate") < 0:
                complete_rate_count += group.get("complete_rate_count")
            elif group.get("complete_rate") == False:
                new_group.append({
                    'complete_rate_count': group.get("complete_rate_count"),
                    'complete_rate': 0,
                })
            else:
                new_group.append(group)

        new_group.append({"complete_rate": complete_rate or 0,
                          "complete_rate_count": complete_rate_count})
        # group_complete[0].pop("__domain")
        group_done = {}
        if group_complete:
            group_done = group_complete[0]
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"complete_rate": new_group or 0,
                                                                    "state": group_done})

    @http.route('/linkloving_app_api/do_unreserve_action', type='json', auth='none', csrf=False)
    def do_unreserve_action(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        picking = request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).search([("id", "=", picking_id)])
        if picking:
            picking.do_unreserve()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.stock_picking_to_json(picking))

    @http.route('/linkloving_app_api/get_outgoing_stock_picking_list', type='json', auth='none', csrf=False)
    def get_outgoing_stock_picking_list(self, **kw):
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        state = request.jsonrequest.get("state")
        complete_rate = request.jsonrequest.get("complete_rate")
        partner_id = request.jsonrequest.get('partner_id')
        domain = [("picking_type_code", "=", "outgoing")]
        # expression.AND([domain, [("picking_type_code", "=", "outgoing")]])
        # request.env["stock.picking"].sudo().search([("state", "in", ("partially_available", "assigned", "confirmed")),
        #                                             ("picking_type_code", "=", "outgoing")])._compute_complete_rate()
        if state:
            domain = expression.AND([domain, [("state", "=", state)]])
        else:
            if complete_rate == 100 or complete_rate == 0:
                domain = expression.AND([domain, [("complete_rate", "=", int(complete_rate)),
                                                  ("state", "in", ["partially_available", "assigned", "confirmed"])]])
            if complete_rate == 99:
                domain = expression.AND([domain, ['&', '&', ("complete_rate", "<", 100), ("complete_rate", ">", 0),
                                                  ("state", "in", ["partially_available", "assigned", "confirmed"])]])
                domain = expression.OR([domain, [("complete_rate", "<", 0)]])

        if partner_id:
            domain = expression.AND([domain, [("partner_id", "child_of", partner_id)]])

        if not state:
            request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).search(domain)._compute_complete_rate()

        picking_list = request.env['stock.picking'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain,
                                                                                                 limit=limit,
                                                                                                 offset=offset,
                                                                                                 order='name desc')

        json_list = []
        for picking in picking_list:
            json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 搜索stock picking
    @http.route('/linkloving_app_api/search_stock_picking_name', type='json', auth='none', csrf=False, cors='*')
    def search_stock_picking_name(self):
        name = request.jsonrequest.get("name")
        domain = [('name', 'ilike', name), ('state', '=', 'validate'), ('picking_type_code', '=', 'incoming')]
        picking_list = request.env['stock.picking'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain, limit=10,
                                                                                                 offset=0,
                                                                                                 order='id desc')
        json_list = []
        for picking in picking_list:
            json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)
        # 搜索stock picking

    @http.route('/linkloving_app_api/search_stock_picking', type='json', auth='none', csrf=False, cors='*')
    def search_stock_picking(self):
        eventId = request.jsonrequest.get("eventId")
        text = request.jsonrequest.get("text")
        uid = request.jsonrequest.get("uid")
        domain = []
        domain.append(('picking_type_code', '=', "incoming"))
        domain.append(("state", "=", "validate"))
        if eventId == 1:
            domain.append(("partner_id", "child_of", text))
        elif eventId == 2:
            domain.append(("origin", "ilike", text))
        elif eventId == 3:
            domain.append(("product_id", "ilike", text))
        picking_list = request.env['stock.picking'].sudo(uid).search(domain, order='id desc')
        json_list = []
        for picking in picking_list:
            json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 获取stock.PICKING列表
    @http.route('/linkloving_app_api/get_stock_picking_list', type='json', auth='none', csrf=False, cors='*')
    def get_stock_picking_list(self, **kw):
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        picking_type_id = request.jsonrequest.get('picking_type_id')
        partner_id = request.jsonrequest.get('partner_id')
        state = request.jsonrequest.get("state")
        uid = request.jsonrequest.get("uid")
        domain = []
        if type(picking_type_id) == list:
            domain.append(('picking_type_id', 'in', picking_type_id))
        else:
            domain.append(('picking_type_id', '=', picking_type_id))
        domain.append(('state', '=', state))
        if partner_id:
            domain.append(('partner_id', 'child_of', partner_id))
        if uid:
            picking_list = request.env['stock.picking'].sudo(uid).search(domain, limit=limit, offset=offset,
                                                                         order='name desc')
        else:
            picking_list = request.env['stock.picking'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain,
                                                                                                     limit=limit,
                                                                                                     offset=offset,
                                                                                                     order='name desc')
        json_list = []
        for picking in picking_list:
            json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    @http.route('/linkloving_app_api/action_assign_stock_picking', type='json', auth='none', csrf=False)
    def action_assign_stock_picking(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        is_check_all = request.jsonrequest.get("check_all")
        if is_check_all:
            pickings = request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).search(
                [("state", "in", ["partially_available", "assigned", "confirmed"]),
                 ("picking_type_code", "=", "outgoing")])
            pickings.force_assign()
            return JsonResponse.send_response(STATUS_CODE_OK, res_data={})

        picking = request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).search([("id", "=", picking_id)])
        try:
            picking.force_assign()
        except UserError:
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.stock_picking_to_json(picking))

    @http.route('/linkloving_app_api/force_assign', type='json', auth='none', csrf=False)
    def force_assign(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        picking = request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).search([("id", "=", picking_id)])
        if picking:
            # pickings = request.env["stock.picking"].sudo().search(
            #         [("state", "in", ["partially_available", "assigned"]),
            #          ("picking_type_code", "=", "outgoing")])
            # picking_un_start_prepare = pickings.is_start_prepare()
            # move_line_available = picking.move_lines.filtered(lambda move: move.state not in [("state", "not in", ["done", "cancel", "assigned"])])
            # # for move_line in move_line_available:
            #     # picking_contain = picking_un_start_prepare.contain_product(move_line.)
            picking.force_assign()
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "找不到对应id的单据"})
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.stock_picking_to_json(picking))

    # 根据销售还是采购来获取stock.picking 出入库
    @http.route('/linkloving_app_api/get_incoming_outgoing_stock_picking', type='json', auth='none', csrf=False)
    def get_incoming_outgoing_stock_picking(self, **kw):
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        picking_type_code = request.jsonrequest.get('picking_type_code')
        state = request.jsonrequest.get("state")
        domain = []
        domain.append(('state', '=', state))  # picking
        if picking_type_code:
            domain.append(('picking_type_code', '=', picking_type_code))

        picking_list = request.env['stock.picking'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain, limit=limit,
                                                                                                 offset=offset,
                                                                                                 order='name desc')
        json_list = []
        for picking in picking_list:
            json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 查看bom详情
    @http.route('/linkloving_app_api/get_bom_detail', type='json', auth="none", csrf=False)
    def get_bom_detail(self, **kw):
        order_id = request.jsonrequest.get("order_id")

        order = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).browse(order_id)

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=order.bom_id.get_bom())

    @http.route('/linkloving_app_api/reassign_pack_done_qty', type='json', auth='none', csrf=False)
    def reassign_pack_done_qty(self, **kw):
        pack_id = request.jsonrequest.get('pack_id')  # 订单id
        new_qty_done = request.jsonrequest.get('new_qty_done')
        pack_op = request.env["stock.pack.operation"].sudo(LinklovingAppApi.CURRENT_USER()).browse(int(pack_id))
        if pack_op.picking_id.state not in ["done", "cancel"]:
            pack_op.qty_done = new_qty_done

            # if pack_op.picking_id.pack_operation_product_ids and \
            #     sum(pack_op.picking_id.pack_operation_product_ids.mapped("qty_done")) == 0:
            #     # 如果所有的pack都为空了,就把这个出货单,置回可用
            #     pack_op.picking_id.state = 'assigned'
        else:
            raise UserError(u"该条目已经出货,不能做此操作")
        return JsonResponse.send_response(STATUS_CODE_OK)

    @http.route('/linkloving_app_api/change_stock_picking_state', type='json', auth='none', csrf=False, cors='*')
    def change_stock_picking_state(self, **kw):
        state = request.jsonrequest.get('state')  # 状态
        picking_id = request.jsonrequest.get('picking_id')  # 订单id
        print LinklovingAppApi.CURRENT_USER()

        pack_operation_product_ids = request.jsonrequest.get('pack_operation_product_ids', [])  # 修改
        i = 0
        for pacl in pack_operation_product_ids:
            if pacl['pack_id'] == -1:
                pack_operation_product_ids.pop(i)
            i = i + 1
        # if not pack_operation_product_ids:
        #     return JsonResponse.send_response(STATUS_CODE_ERROR,
        #                                       res_data={'error': _("Pack Order not found")})

        pack_list = request.env['stock.pack.operation'].sudo(LinklovingAppApi.CURRENT_USER()).search(
            [('id', 'in', map(lambda a: a['pack_id'], pack_operation_product_ids))])

        # 仓库或者采购修改了数量
        qty_done_map = map(lambda a: a['qty_done'], pack_operation_product_ids)
        rejects_qty_map = map(lambda a: a.get('rejects_qty') or 0, pack_operation_product_ids)

        def x(a, b):
            if not a:
                raise UserError(u"找不到对应的出货单")
            a.qty_done = b

        def y(a, b):
            a.rejects_qty = b

        map(x, pack_list, qty_done_map)
        map(y, pack_list, rejects_qty_map)

        picking_obj = request.env['stock.picking'].sudo(LinklovingAppApi.CURRENT_USER()).search(
            [('id', '=', picking_id)])
        if picking_obj.state == 'cancel':
            raise UserError(u'该单据已取消,无法操作')
        if state == 'confirm':  # 确认 标记为代办
            picking_obj.action_confirm()
        elif state == 'post':  # 提交
            post_img = request.jsonrequest.get('post_img')
            post_area_name = request.jsonrequest.get('post_area_name')
            area = request.env['stock.location.area'].sudo().search([('name', '=', post_area_name)])
            if not area:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={'error': _("Please choose the right location")})
            picking_obj.post_img = post_img
            picking_obj.post_area_id = area[0].id

            picking_obj.action_post()
        elif state == 'cancel':  # 取消
            picking_obj.action_cancel()
        elif state == 'qc_ok' or state == 'qc_failed':  # 品检结果
            qc_note = request.jsonrequest.get('qc_note')
            qc_img = request.jsonrequest.get('qc_img')
            picking_obj.qc_note = qc_note
            picking_obj.qc_img = qc_img
            if state == 'qc_ok':
                picking_obj.action_check_pass()
            elif state == 'qc_failed':
                picking_obj.action_check_fail()

        elif state == 'reject':  # 退回
            picking_obj.reject()
        elif state == 'to_picking':  # 退回
            picking_obj.to_picking()
        elif state == 'process':  # 创建欠单
            #### 判断库存是否不够
            if picking_obj.picking_type_code == "outgoing":
                for pack in pack_list:
                    if pack.qty_done > pack.product_id.qty_available:
                        return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                          res_data={
                                                              "error": u"%s 产品库存不足,无法完成出货" % pack.product_id.display_name})

                wiz = request.env['stock.backorder.confirmation'].sudo(LinklovingAppApi.CURRENT_USER()).create(
                    {'pick_id': picking_id})
                is_yes = request.jsonrequest.get("qc_note")  # 货是否齐
                if picking_obj.sale_id:
                    if (picking_obj.sale_id.delivery_rule == "delivery_once" or not picking_obj.sale_id.delivery_rule) \
                            and is_yes != "yes":
                        return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                          res_data={"error": u"该销售单需要一次性发完货,请等待货齐后再发"})
                    elif picking_obj.sale_id.delivery_rule == "delivery_once" and picking_obj.state not in ["assigned",
                                                                                                            "secondary_operation_done",
                                                                                                            "waiting_out"]:
                        return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                          res_data={"error": u"该单据为部分可用,请等待货齐后再发"})
                    elif picking_obj.sale_id.delivery_rule == "cancel_backorder":  # 取消欠单
                        wiz.process_cancel_backorder()
                        picking_obj.to_stock()

                    elif picking_obj.sale_id.delivery_rule == "create_backorder":  # 创建欠单
                        wiz.process()
                        picking_obj.to_stock()
                    elif picking_obj.sale_id.delivery_rule == "delivery_once" and is_yes == "yes" and picking_obj.state in [
                        "assigned", "secondary_operation_done", "waiting_out"]:  # 一次性出货并备货完成
                        wiz.process()
                        picking_obj.to_stock()
                else:
                    return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                      res_data={"error": "此单据未关联任何销售单!"})
            elif picking_obj.picking_type_code == "incoming":
                wiz = request.env['stock.backorder.confirmation'].sudo(LinklovingAppApi.CURRENT_USER()).create(
                    {'pick_id': picking_id})
                wiz.process()
        elif state == 'picking_done':
            picking_obj.action_picking_done()
        elif state == 'cancel_backorder':  # 取消欠单\
            wiz = request.env['stock.backorder.confirmation'].sudo(LinklovingAppApi.CURRENT_USER()).create(
                {'pick_id': picking_id})
            wiz.process_cancel_backorder()
        elif state == 'transfer_way':  # 入库方式: 全部入库 or 良品入库
            is_all = request.jsonrequest.get("is_all")
            if is_all == 'all':
                is_all_in = True
            elif is_all == 'part':
                is_all_in = False
            else:
                raise UserError(u"请选择入库方式")
            request.env["stock.transfer.way"].with_context({'is_all_transfer_in': is_all_in}).sudo().create({
                'picking_id': picking_obj.id,
            }).choose_transfer_way()
            # way.with_context({'is_all_transfer_in': is_all_in}).choose_transfer_way()
        elif state == 'transfer':  # 入库
            picking_obj.to_stock()
        elif state == 'cancel_stock':  # 开始备货
            picking_obj.state = 'assigned'
        elif state == 'stock_ready':  # 备货完成
            picking_obj.stock_ready()
        elif state == 'upload_img':
            express_img = request.jsonrequest.get('qc_img')
            DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
            self.add_file_to_attachment(express_img,
                                        "express_img_%s.png" % time.strftime(DEFAULT_SERVER_DATE_FORMAT,
                                                                             time.localtime()),
                                        "stock.picking", picking_id)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.stock_picking_to_json(picking_obj))

    def add_file_to_attachment(self, ufile, file_name, model, id):
        Model = request.env['ir.attachment'].sudo(LinklovingAppApi.CURRENT_USER())
        attachment = Model.create({
            'name': file_name,
            'datas': ufile,
            'datas_fname': file_name,
            'res_model': model,
            'res_id': id
        })
        return attachment

    @classmethod
    def is_has_attachment(self, res_id, res_model):
        Model = request.env['ir.attachment'].sudo(LinklovingAppApi.CURRENT_USER())
        attach = Model.search([("res_id", "=", res_id),
                               ("res_model", "=", res_model)])
        # http://localhost:8069/web/content/1826?download=true
        if attach:
            return True
        else:
            return False

    @classmethod
    def get_product_image_url_new(cls, product_product, model):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        url = '%spayment/order_status?pidsss=%s&model=%s' % \
              (request.httprequest.host_url, str(product_product), model)

        return url

    @classmethod
    def stock_picking_to_json(cls, stock_picking_obj):
        pack_list = []
        move_lines = stock_picking_obj.move_lines
        # quants = request.env["stock.quant"]
        # if stock_picking_obj.picking_type_code == 'outgoing':
        #     quants = stock_picking_obj.reserveration_qty()
        for pack in stock_picking_obj.pack_operation_product_ids:
            dic = {
                'pack_id': pack.id,
                'product_id': {
                    'id': pack.product_id.id,
                    'name': pack.product_id.display_name,
                    'default_code': pack.product_id.default_code,
                    'qty_available': pack.product_id.qty_available,
                    'product_specs': pack.product_id.product_specs or '',
                    'weight': pack.product_id.weight or 0,
                    'area_id': {
                        'area_id': pack.product_id.area_id.id or None,
                        'area_name': pack.product_id.area_id.name or None,
                    },
                    'image_ids': [
                        {'image_url': LinklovingAppApi.get_product_image_url_new(urlBean.id, 'ir.attachment')}
                        for urlBean in pack.product_id.product_img_ids]
                },
                'product_qty': pack.product_qty,
                'qty_done': pack.qty_done,
                'to_location': pack.to_loc,
                'rejects_qty': pack.rejects_qty,
            }
            dic.update(cls.get_reserved_pack(pack.product_id, pack.picking_id.id))

            move_ids = pack.linked_move_operation_ids.mapped("move_id")
            # if move_ids and quants:
            #     if quants.get(move_ids[0].id):
            #         quant = quants.get(move_ids[0].id).filtered(lambda x: x.reservation_id.id not in move_lines.ids)
            #         if quant:
            #             pack_products = quant.mapped("reservation_id") and\
            #             quant.mapped("reservation_id").mapped("picking_id") and \
            #             quant.mapped("reservation_id").mapped("picking_id").mapped("pack_operation_product_ids")
            #             packs = []
            #             for pack1 in pack_products:
            #                 if pack1.product_id == pack.product_id:
            #                     packs.append({
            #                         'id': pack1.id,
            #                         'origin': pack1.picking_id.origin or '',
            #                         'pick_name': pack1.picking_id.name,
            #                         'qty_done': pack1.qty_done,
            #                         'partner_name': pack1.picking_id.partner_id.name,
            #                         'product_name': pack1.product_id.display_name,
            #                         'product_qty': pack1.product_qty,
            #                     })
            #             dic["reserved_picking_ids"] = packs
            #         else:
            #             dic["reserved_picking_ids"] = []
            #         reserved_qty = sum(quant.mapped("qty") if quant else [])
            #         dic["reserved_qty"] = reserved_qty
            origin_qty = 0
            for move in move_ids:
                # if len(move_ids) == 1:
                origin_qty += move.product_uom_qty
                if move in move_lines:
                    move_lines -= move
            dic["origin_qty"] = origin_qty
            pack_list.append(dic)
        for move in move_lines.filtered(lambda x: x.state != 'cancel'):
            dic = {
                'pack_id': -1,
                'product_id': {
                    'id': move.product_id.id,
                    'name': move.product_id.display_name,
                    'default_code': move.product_id.default_code,
                    'qty_available': move.product_id.qty_available,
                    'weight': move.product_id.weight or 0,
                    'area_id': {
                        'area_id': move.product_id.area_id.id or None,
                        'area_name': move.product_id.area_id.name or None,
                    },
                    'image_ids':
                        [
                        ]
                },
                'product_qty': 0,
                'qty_done': 0,
                'origin_qty': move.product_uom_qty,
            }
            dic.update(cls.get_reserved_pack(move.product_id, -1))
            # if move and quants:
            #     if quants.get(move.id):
            #         quant = quants.get(move.id).filtered(lambda x: x.reservation_id.id not in move_lines.ids)
            #         reserved_qty = sum(quant.mapped("qty") if quant else [])
            #         dic["reserved_qty"] = reserved_qty  #
            #         if quant:
            #             pack_products = quant.mapped("reservation_id") and\
            #             quant.mapped("reservation_id").mapped("picking_id") and \
            #             quant.mapped("reservation_id").mapped("picking_id").mapped("pack_operation_product_ids")
            #             packs = []
            #             for pack in pack_products:
            #                 if pack.product_id == move.product_id:
            #                     packs.append({
            #                         'id': pack.id,
            #                         'origin': pack.picking_id.origin or '',
            #                         'pick_name': pack.picking_id.name,
            #                         'qty_done': pack.qty_done,
            #                         'partner_name': pack.picking_id.partner_id.name,
            #                         'product_name': pack.product_id.display_name,
            #                         'product_qty': pack.product_qty,
            #                     })
            #             dic["reserved_picking_ids"] = packs
            #         else:
            #             dic["reserved_picking_ids"] = []
            pack_list.append(dic)
        data = {
            'secondary_operation': stock_picking_obj.secondary_operation,  # zou增，下，
            'timesheet_order_id': LinklovingAppApi.timesheet_order_ids_json(
                stock_picking_obj.timesheet_order_ids.filtered(lambda x: x.state == 'running'))
            if stock_picking_obj.state == 'secondary_operation' else LinklovingAppApi.timesheet_order_ids_json(
                stock_picking_obj.timesheet_order_ids),
            'picking_id': stock_picking_obj.id,
            'complete_rate': stock_picking_obj.complete_rate or 0,
            'has_attachment': LinklovingAppApi.is_has_attachment(stock_picking_obj.id, 'stock.picking'),
            'sale_note': stock_picking_obj.sale_id.remark,
            'delivery_rule': stock_picking_obj.delivery_rule or None,
            'picking_type_code': stock_picking_obj.picking_type_code,
            'name': stock_picking_obj.name,
            'parnter_id': stock_picking_obj.partner_id.display_name,
            'phone': stock_picking_obj.partner_id.mobile or stock_picking_obj.partner_id.phone or '',
            'origin': stock_picking_obj.origin or '',
            'state': stock_picking_obj.state,

            'back_order_id': stock_picking_obj.backorder_id.name or '',
            'emergency': stock_picking_obj.is_emergency or '',
            'creater': stock_picking_obj.sudo().create_uid.name or '',
            'location_id': stock_picking_obj.location_id.complete_name or '',
            'tracking_number': stock_picking_obj.tracking_number or '',

            'move_type': stock_picking_obj.move_type,  # 交货类型
            'picking_type': {
                'picking_type_id': stock_picking_obj.picking_type_id.id,
                'picking_type_name': stock_picking_obj.picking_type_id.name
            },  # 分拣类型
            'group_id': stock_picking_obj.group_id.name,  # 补货组
            'priority': stock_picking_obj.priority,  # 优先级
            'carrier': stock_picking_obj.carrier_id.name or '',  # 承运商
            'carrier_tracking_ref': stock_picking_obj.carrier_tracking_ref or '',  # 跟踪参考
            'weight': stock_picking_obj.weight,  # 重量
            'shipping_weight': stock_picking_obj.shipping_weight,  # 航空重量
            'number_of_packages': stock_picking_obj.number_of_packages,  # 包裹件数
            'min_date': stock_picking_obj.min_date,
            'pack_operation_product_ids': pack_list,
            'qc_note': stock_picking_obj.qc_note or '',
            'qc_result': stock_picking_obj.qc_result,
            'qc_img': LinklovingAppApi.get_stock_picking_img_url(stock_picking_obj.id, 'qc_img'),
            'post_img': LinklovingAppApi.get_stock_picking_img_url(stock_picking_obj.id, 'post_img'),
            'post_area_id':
                {
                    'area_id': stock_picking_obj.post_area_id.id or None,
                    'area_name': stock_picking_obj.post_area_id.name or None,
                }
        }
        return data

    @classmethod
    def get_reserved_pack(cls, product_id, picking_id):
        res_dic = {}
        pickings = request.env["stock.picking"].sudo().search([('state', 'not in', ['done', 'cancel', 'confirmed']),
                                                               ('picking_type_code', '=', 'outgoing'),
                                                               ('product_id', '=', product_id.id),
                                                               ('id', '!=', picking_id)])
        reserved_qty = 0
        if pickings:
            packs = []
            for pack_op in pickings.mapped("pack_operation_product_ids").filtered(
                    lambda x: x.product_id == product_id and x.qty_done > 0):
                packs.append({
                    'id': pack_op.id,
                    'origin': pack_op.picking_id.origin or '',
                    'pick_name': pack_op.picking_id.name,
                    'qty_done': pack_op.qty_done,
                    'partner_name': pack_op.picking_id.partner_id.name,
                    'product_name': pack_op.product_id.display_name,
                    'product_qty': pack_op.product_qty,
                })
                reserved_qty += pack_op.qty_done
            res_dic["reserved_picking_ids"] = packs
        else:
            res_dic["reserved_picking_ids"] = []
        res_dic["reserved_qty"] = reserved_qty
        return res_dic

    @classmethod
    def get_stock_picking_img_url(cls, picking_id, field):
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
            request.httprequest.host_url, str(picking_id), 'stock.picking', field)
        if not url:
            return ''
        return url

    # 搜索供应商
    @http.route('/linkloving_app_api/search_supplier', type='json', auth='none', csrf=False)
    def search_supplier(self, **kw):
        name = request.jsonrequest.get('name')
        partner_type = request.jsonrequest.get('type')  # supplier or customer
        domain = []
        if name:
            domain.append(('name', 'ilike', name))
        if partner_type:
            domain.append((partner_type, '=', True))
        lists = request.env['res.partner'].sudo().search(domain)
        json_list = []
        for l in lists:
            json_list.append(LinklovingAppApi.res_partner_to_json(l))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    @classmethod
    def res_partner_to_json(cls, res_partner, exact_dict=None):
        data = {
            'partner_id': res_partner.id,
            'name': res_partner.name or '',
            'phone': res_partner.phone or '',
            'comment': res_partner.comment or '',
            'x_qq': res_partner.x_qq or '',
        }
        data.update(exact_dict or {})
        return data

    @classmethod
    def loadMenus(self):
        menu_model = request.env['ir.ui.menu']
        fields = ['name', 'sequence', 'parent_id', 'action', 'web_icon']
        menu_roots = menu_model.search([('parent_id', '=', False), ('is_show_on_app', '=', True)])
        menu_roots_data = menu_roots.read(fields) if menu_roots else []
        menu_root = {
            'id': False,
            'name': 'root',
            'parent_id': [-1, ''],
            'children': menu_roots_data,
            'all_menu_ids': menu_roots.ids,
        }
        if not menu_roots_data:
            return menu_root

        # menus are loaded fully unlike a regular tree view, cause there are a
        # limited number of items (752 when all 6.1 addons are installed)
        menus = menu_model.search([('id', 'child_of', menu_roots.ids), ('is_show_on_app', '=', True)])

        xml_names = request.env['ir.model.data'].sudo().search_read(
            [('res_id', 'in', menus.ids), ('model', '=', 'ir.ui.menu')], fields=['complete_name', 'res_id'])
        menu_items = menus.read(fields)
        for menu in menu_items:
            menu["app_icon"] = LinklovingAppApi.get_app_menu_icon_img_url(menu['id'], "app_menu_icon")
            for xml in xml_names:
                if menu['id'] == xml['res_id']:
                    menu['xml_name'] = xml['complete_name']
                    break
        # add roots at the end of the sequence, so that they will overwrite
        # equivalent menu items from full menu read when put into id:item
        # mapping, resulting in children being correctly set on the roots.
        menu_items.extend(menu_roots_data)
        menu_root['all_menu_ids'] = menus.ids  # includes menu_roots !

        # make a tree using parent_id
        menu_items_map = {menu_item["id"]: menu_item for menu_item in menu_items}
        for menu_item in menu_items:
            parent = menu_item['parent_id'] and menu_item['parent_id'][0]
            if parent in menu_items_map:
                menu_items_map[parent].setdefault(
                    'children', []).append(menu_item)

        # sort by sequence a tree using parent_id
        for menu_item in menu_items:
            menu_item.setdefault('children', []).sort(key=operator.itemgetter('sequence'))

        return menu_root

    @classmethod
    def get_jpush_tags(cls, type):
        if type == 'qc':  # 品检组 tag
            return 'group_charge_inspection'
        elif type == 'warehouse':  # 仓库组
            return 'group_charge_warehouse'
        elif type == 'produce':  # 生产组
            return 'group_charge_produce'
        elif type == 'purchase_user':  # 采购用户
            return 'group_purchase_user'
        elif type == 'purchase_manager':  # 采购管理员
            return 'group_purchase_manager'

    @http.route('/linkloving_app_api/load_needaction', type='json', auth="none", csrf=False)
    def ll_load_needaction(self):
        """ Loads needaction counters for specific menu ids.

            :return: needaction data
            :rtype: dict(menu_id: {'needaction_enabled': boolean, 'needaction_counter': int})
        """
        # menu_ids = request.jsonrequest.get("menu_ids")
        user_id = request.jsonrequest.get("user_id")
        xml_names = request.jsonrequest.get("xml_names")
        if xml_names:
            # needaction_data = request.env['ir.ui.menu'].sudo(user_id).browse(menu_ids).get_needaction_data()
            # needaction_data = request.env['ir.ui.menu'].sudo(user_id).search([("", "", )]).get_needaction_data()
            menu_ids = []
            for xml_name in xml_names:
                list = xml_name.split(".")
                if len(list) >= 2:
                    menu_id = request.env['ir.model.data'].sudo().search_read(
                        [('name', '=', list[1]),
                         ('module', '=', list[0]),
                         ('model', '=', 'ir.ui.menu')], fields=['res_id'])
                if menu_id:
                    menu_ids.append(menu_id[0]["res_id"])

            needaction_menus = request.env['ir.ui.menu'].sudo(user_id).browse(menu_ids)
            needaction_data = LinklovingAppApi.get_needaction_data(needaction_menus, user_id)
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=needaction_data)

    @classmethod
    def get_needaction_data(cls, needaction_menus, uid):
        """ Return for each menu entry in ``self``:
            - whether it uses the needaction mechanism (needaction_enabled)
            - the needaction counter of the related action, taking into account
              the action domain
        """
        # menu_ids = set()
        # for menu in needaction_menus:
        #     menu_ids.add(menu.id)
        res = {}
        xml_names = request.env['ir.model.data'].sudo().search_read(
            [('res_id', 'in', needaction_menus.ids), ('model', '=', 'ir.ui.menu')],
            fields=['complete_name', 'res_id'])
        for menu in needaction_menus:
            xml_name = None
            for item in xml_names:
                if item["res_id"] == menu.id:
                    xml_name = item["complete_name"]
            res[xml_name] = {
                'needaction_enabled': False,
                'needaction_counter': False,
            }
            if menu.action and menu.action.type in (
                    'ir.actions.act_window', 'ir.actions.client') and menu.action.res_model:
                model = request.env[menu.action.res_model].sudo(user=uid)
                if menu.action.context != u'{}':
                    try:
                        model = request.env[menu.action.res_model].sudo(user=uid).with_context(
                            **eval(menu.action.context.strip()))
                    except Exception:
                        pass

                if model._needaction:
                    if menu.action.type == 'ir.actions.act_window':
                        eval_context = request.env['ir.actions.act_window'].sudo(user=uid)._get_eval_context()
                        dom = safe_eval(menu.action.domain or '[]', eval_context)
                    else:
                        dom = safe_eval(menu.action.params_store or '{}', {'uid': uid}).get('domain')
                    res[xml_name]['needaction_enabled'] = model._needaction
                    res[xml_name]['needaction_counter'] = model._needaction_count(dom)
        print(res)
        return res

        # if __name__ == '__main__':
        #         domain = ['|', ('in_charge_id', '=', 1),('create_uid', '=', 1)]
        #
        #         domain_delay = [('date_planned_start', '<', fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        #
        #                  ('state', 'in', ['already_picking']),
        #                  # ('process_id', '=', process_id),
        #                  # ('location_ids', 'in', location_domain)
        #                  ]
        #         domain_delay = expression.AND([domain_delay,domain])

    @http.route('/linkloving_app_api/update_factory_remark', type='json', auth='none', csrf=False)
    def update_factory_remark(self, **kw):
        order_id = request.jsonrequest.get("order_id")
        remark = request.jsonrequest.get("factory_remark")

        order = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).browse(order_id)
        order.factory_remark = remark

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})

    @http.route('/linkloving_app_api/get_factory_remark', type='json', auth='none', csrf=False)
    def get_factory_remark(self, **kw):
        order_id = request.jsonrequest.get("order_id")

        order = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).browse(order_id)

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={"factory_mark": order.factory_remark or ''})

    @http.route('/linkloving_app_api/create_material_remark', type='json', auth='none', csrf=False)
    def create_material_remark(self, **kw):
        content = request.jsonrequest.get("content")
        remark_type = request.jsonrequest.get("type")
        if not remark_type:
            remark_type = 'material'
        remark = request.env["material.remark"].sudo(LinklovingAppApi.CURRENT_USER()).create({
            "content": content,
            "type": remark_type,
        })
        all_remarks = request.env["material.remark"].sudo(LinklovingAppApi.CURRENT_USER()).search_read([])
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=all_remarks)

    @http.route('/linkloving_app_api/get_material_remark', type='json', auth='none', csrf=False)
    def get_material_remark(self, **kw):
        remark_type = request.jsonrequest.get("type")
        remarks = request.env["material.remark"].sudo(LinklovingAppApi.CURRENT_USER()).search_read(
            [("type", "=", remark_type)])
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=remarks)

    @http.route('/linkloving_app_api/add_material_remark', type='json', auth='none', csrf=False)
    def add_material_remark(self, **kw):
        order_id = request.jsonrequest.get("order_id")
        remark_id = request.jsonrequest.get("remark_id")

        order = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).browse(order_id)
        if order.state in ["waiting_material", "prepare_material_ing"]:
            order.material_remark_id = remark_id
        elif order.state in ["finish_prepare_material", "already_picking", "progress"]:
            order.production_remark_id = remark_id
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": u"该状态不能做此操作"})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})

    @http.route('/linkloving_oa_api/get_origin/', auth='none', type='http', csrf=False)
    def get_origin(self, **kwargs):
        # request.session.db = '0426'#'#request.jsonrequest["db"]
        # request.params["db"] = '0426'#request.jsonrequest["db"]

        sources = request.env["crm.lead.source"].sudo(LinklovingAppApi.CURRENT_USER()).search_read([], fields=['name'])
        print sources
        return sources

    ######### 销售出货 新版接口  ###############3
    # 销售团队
    @http.route('/linkloving_app_api/get_sale_team/', auth='user', type='json', csrf=False)
    def get_sale_team(self, **kwargs):
        sale_teams = request.env["crm.team"].sudo(LinklovingAppApi.CURRENT_USER()).search([])

        json_list = []
        for team in sale_teams:
            data = {
                'team_id': team.id,
                'name': team.name,
            }
            json_list.append(data)

        json_list.append({"team_id": -999,
                          "name": u"未定义"})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=json_list)

    # 根据销售团队获取客户
    @http.route('/linkloving_app_api/get_partner_by_team/', auth='user', type='json', csrf=False)
    def get_partner_by_team(self, **kwargs):
        team_id = request.jsonrequest.get("team_id")
        name = request.jsonrequest.get("name")
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        # self.a(team_id)
        domain = [('is_company', '=', True), ('customer', '=', True)]
        if team_id:
            if team_id == -999:
                domain = expression.AND([domain, [('team_id', '=', None)]])
            else:
                domain = expression.AND([domain, [('team_id', '=', team_id)]])
        if name:
            domain = expression.AND([domain, [('name', 'ilike', name)]])
        partners = request.env["res.partner"].sudo().search(domain)
        partners = partners.filtered(lambda x: x.sale_order_count > 0)
        json_list = []
        print("start:%s" % fields.datetime.utcnow())
        for partner in partners:
            picing_info = self.get_picking_info_by_partner(partner.id)
            if len(picing_info["waiting_data"]):
                json_list.append(LinklovingAppApi.res_partner_to_json(partner, exact_dict={
                    'waiting_data': len(picing_info["waiting_data"]),
                    'able_to_data': len(picing_info["able_to_data"])}))
        print("end:%s" % fields.datetime.utcnow())
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=json_list)

    # 单号搜索
    @http.route('/linkloving_app_api/get_picking_by_origin/', auth='user', type='json', csrf=False)
    def get_picking_by_origin(self, **kwargs):
        order_name = request.jsonrequest.get("order_name")
        domain = [("origin", 'ilike', order_name), ('picking_type_code', '=', 'outgoing'), ]
        # domain = expression.OR([domain, [('name', 'ilike', order_name)]])
        pickings = request.env["stock.picking"].sudo().search(domain)

        json_list = self.get_picking_info_by_picking(pickings)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=json_list)

    # 搜索完成的单据
    @http.route('/linkloving_app_api/get_done_picking/', auth='user', type='json', csrf=False)
    def get_done_picking(self, **kwargs):
        partner_id = request.jsonrequest.get("partner_id")
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")

        domain = [('partner_id', 'child_of', partner_id), ('picking_type_code', '=', 'outgoing'),
                  ("state", '=', 'done')]
        pickings = request.env["stock.picking"].sudo(LinklovingAppApi.CURRENT_USER()).search(domain, limit=limit,
                                                                                             offset=offset)
        json_list = []
        for picking in pickings:
            json_list.append(self.stock_picking_to_json_simple(picking))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=json_list)

    # 根据客户搜索
    @http.route('/linkloving_app_api/get_stock_picking_by_partner/', auth='user', type='json', csrf=False)
    def get_stock_picking_by_partner(self, **kwargs):
        partner_id = request.jsonrequest.get("partner_id")

        json_list = self.get_picking_info_by_partner(partner_id)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=json_list)

    def get_picking_info_by_partner(self, partner_id):
        domain = [('partner_id', 'child_of', partner_id), ('picking_type_code', '=', 'outgoing'),
                  ("state", 'not in', ['cancel', 'done'])]
        pickings = request.env["stock.picking"].sudo().search(domain, order='create_date desc')
        # if type == 'able_to': #可处理
        print('length =%d' % len(pickings))
        return self.get_picking_info_by_picking(pickings)

    def get_picking_info_by_picking(self, pickings):
        final_pickings = request.env["stock.picking"]
        for picking in pickings:
            if picking.state == 'assigned':  # 可用状态的直接就是可处理
                final_pickings += picking
                continue
            if picking.available_rate > 0 and picking.available_rate < 100:
                if picking.delivery_rule != 'delivery_once' and picking.state != 'waiting':  # 不是一次性发货并且 不是等待其他作业的状态
                    final_pickings += picking
            elif picking.available_rate == 100 and picking.state != 'waiting':  # 可用率为100 并且不是等待其他作业的状态
                final_pickings += picking

        json_list = {'waiting_data': [],
                     'able_to_data': []}
        for picking in final_pickings:
            json_list['able_to_data'].append(self.stock_picking_to_json_simple(picking))

        for picking in pickings:
            json_list['waiting_data'].append(self.stock_picking_to_json_simple(picking))
        return json_list

    def stock_picking_to_json_simple(self, picking):
        data = {
            'picking_id': picking.id,
            'has_attachment': LinklovingAppApi.is_has_attachment(picking.id, 'stock.picking'),
            'name': picking.name,
            'origin': picking.origin,
            'state': picking.state,
            'back_order_id': picking.backorder_id.name or '',
            'emergency': picking.is_emergency or '',
            'partner_id': picking.partner_id.name,
            'secondary_operation': picking.secondary_operation,  # zou增，下同
            'timesheet_order_ids': self.timesheet_order_ids_json(
                picking.timesheet_order_ids.filtered(lambda x: x.state == 'running'))
            if picking.state == 'secondary_operation' else LinklovingAppApi.timesheet_order_ids_json(
                picking.timesheet_order_ids),
        }
        return data

    # zou增加解析json二次加工信息
    @classmethod
    def timesheet_order_ids_json(cls, timesheet_order_id):
        time_list = []
        for time_id in timesheet_order_id:
            data = {
                'id': time_id.id or 0,
                'from_partner': {
                    "id": time_id.from_partner.id or 0,
                    "name": time_id.from_partner.name or ''
                },
                'to_partner': {
                    "id": time_id.to_partner.id or 0,
                    "name": time_id.to_partner.name or ''
                },
                'work_type_id': {
                    "id": time_id.work_type_id.id or 0,
                    "name": time_id.work_type_id.name or ''
                },
                'hour_spent': time_id.hour_spent or 0
            }
            time_list.append(data)
        return time_list
        ######### 生产 新版接口  ###############

    # 备料完成
    @http.route('/linkloving_app_api/new_finish_prepare_material', type='json', auth='none', csrf=False)
    def new_finish_prepare_material(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = \
            request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', order_id)])[0]

        # stock_moves = request.jsonrequest.get('stock_move') #get paramter
        # stock_move_lines = request.env["sim.stock.move"].sudo()
        # mrp_production.write({'state': 'finish_prepare_material'})
        mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write({'state': 'already_picking',
                                                                               'picking_material_date': fields.datetime.now()})
        # _logger.warning(u"charlie_0712_log10:finish, mo:%s", LinklovingAppApi.model_convert_to_dict(order_id, request))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 备料
    @http.route('/linkloving_app_api/new_prepare_material', type='json', auth='none', csrf=False)
    def new_prepare_material1(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        employee_id = request.jsonrequest.get("employee_id")
        uid = request.context.get("uid")
        stock_moves = [request.jsonrequest.get('stock_move')]  # get paramter
        # _logger.warning(u"charlie_0712_log:finish_prepare_material, mo:%s,moves:%s", mrp_production.name, stock_moves)
        # print(u"charlie_0712_log:finish_prepare_material, mo:%s,moves:%s" % (mrp_production.name, stock_moves))
        stock_move_lines = request.env["sim.stock.move"].sudo()
        # try:
        for move in stock_moves:
            sim_stock_move = request.env["sim.stock.move"].sudo().browse(move['stock_move_lines_id'])

            if "quantity_available" in move.keys():
                if move.get("quantity_available") != sim_stock_move.product_id.qty_available:
                    raise UserError(u'在手数量与实际不符,请检查备料情况')
            # LinklovingAppApi.get_model_by_id(,
            #                                                   request,
            #                                                   'sim.stock.move')
            stock_move_lines += sim_stock_move
            if not sim_stock_move.stock_moves:
                continue
            else:
                move_todo = sim_stock_move.stock_moves.filtered(lambda x: x.state not in ["cancel", "done"])
                if not move_todo:
                    split_move = sim_stock_move.stock_moves[0].copy(
                        default={'quantity_done': move['quantity_ready'],
                                 'product_uom_qty': move['quantity_ready'],
                                 'production_id': sim_stock_move.production_id.id,
                                 'raw_material_production_id': sim_stock_move.raw_material_production_id.id,
                                 'procurement_id': sim_stock_move.procurement_id.id or False,
                                 'is_over_picking': True})
                    split_move.write({'state': 'assigned'})
                    # sim_stock_move.production_id.move_raw_ids = sim_stock_move.production_id.move_raw_ids + split_move
                    split_move.action_done()
                    split_move.authorized_stock_move(employee_id, uid)
                elif len(move_todo) > 1:
                    if move_todo[0].state == 'draft':
                        move_todo[0].action_confirm()
                    move_todo[0].quantity_done = move['quantity_ready']
                    move_todo[0].action_done()
                    move_todo[0].authorized_stock_move(employee_id, uid)
                else:
                    if move_todo.state == 'draft':
                        move_todo.action_confirm()
                    move_todo.quantity_done = move['quantity_ready']
                    move_todo.action_done()
                    move_todo.authorized_stock_move(employee_id, uid)
            sim_stock_move.quantity_ready = 0  # 清0
            # sim_stock_move.quantity_done = sim_stock_move.quantity_done + move['quantity_ready']
        # except Exception, e:
        #     return JsonResponse.send_response(STATUS_CODE_ERROR,
        #                                       res_data={"error": e.name})
        # _logger.warning(u"charlie_0712_log10:finish, mo:%s", LinklovingAppApi.model_convert_to_dict(order_id, request))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 备料
    @http.route('/linkloving_app_api/new_prepare_material1', type='json', auth='none', csrf=False)
    def new_prepare_material(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        employee_id = request.jsonrequest.get("employee_id")
        uid = request.context.get("uid")
        # if employee_id:

        # mrp_production = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', order_id)])[0]

        stock_moves = [request.jsonrequest.get('stock_move')]  # get paramter
        # _logger.warning(u"charlie_0712_log:finish_prepare_material, mo:%s,moves:%s", mrp_production.name, stock_moves)
        # print(u"charlie_0712_log:finish_prepare_material, mo:%s,moves:%s" % (mrp_production.name, stock_moves))
        stock_move_lines = request.env["sim.stock.move"].sudo()
        try:
            for move in stock_moves:
                sim_stock_move = LinklovingAppApi.get_model_by_id(move['stock_move_lines_id'], request,
                                                                  'sim.stock.move')
                stock_move_lines += sim_stock_move
                if not sim_stock_move.stock_moves:
                    continue
                if "quantity_available" in move.keys():
                    if move.get("quantity_available") != sim_stock_move.product_id.qty_available:
                        raise UserError(u'在手数量与实际不符,请检查备料情况')
                if move['quantity_ready'] > 0:
                    sim_stock_move.is_prepare_finished = True
                else:
                    continue
                rounding = sim_stock_move.stock_moves[0].product_uom.rounding
                total_qty = move['quantity_ready'] + sim_stock_move.quantity_done
                need_qty = 0
                for o_move in sim_stock_move.stock_moves:
                    if o_move.state != 'cancel':
                        need_qty += o_move.product_uom_qty
                logging.warning("charlie0910--------%d,%d,%d,%d" % (
                    total_qty, need_qty, sim_stock_move.product_uom_qty, sim_stock_move.quantity_done))
                # if float_compare(need_qty, sim_stock_move.product_uom_qty, precision_rounding=rounding) < 0:
                if float_compare(total_qty, sim_stock_move.product_uom_qty, precision_rounding=rounding) > 0:

                    # if float_compare(move['quantity_ready'], sim_stock_move.stock_moves[0].product_uom_qty,
                    #                  precision_rounding=rounding) > 0:
                    # _logger.warning(u"charlie_0712_log_1:move_qty:%s,move_id:%d,uom_qty:%s",
                    #                 str(move['quantity_ready']),
                    #                 sim_stock_move.stock_moves[0].id,
                    #                 str(sim_stock_move.stock_moves[0].product_uom_qty))
                    # 如果已完成的数量大于等于需求数量,则生成的库存移动单的数量就是本次备料的数量
                    if float_compare(sim_stock_move.quantity_done, sim_stock_move.product_uom_qty,
                                     precision_rounding=rounding) >= 0:
                        split_qty_unuom = move['quantity_ready']  # 未经过单位换算的数量
                    else:
                        # 如果已完成的数量大于等于需求数量,则是 总数量 - 需求数量
                        if sim_stock_move.stock_moves.filtered(lambda x: x.state not in ["cancel", "done"]):
                            split_qty_unuom = total_qty - sim_stock_move.product_uom_qty
                        else:
                            split_qty_unuom = total_qty - sim_stock_move.quantity_done

                    qty_split = sim_stock_move.stock_moves[0].product_uom._compute_quantity(
                        split_qty_unuom,
                        sim_stock_move.stock_moves[0].product_id.uom_id)
                    logging.warning("charlie0910-1-------%d,%d" % (split_qty_unuom, qty_split))
                    # _logger.warning(u"charlie_0712_log_2:qty_split:%s,", str(qty_split))
                    split_move = sim_stock_move.stock_moves[0].copy(
                        default={'quantity_done': qty_split, 'product_uom_qty': qty_split,
                                 'production_id': sim_stock_move.production_id.id,
                                 'raw_material_production_id': sim_stock_move.raw_material_production_id.id,
                                 'procurement_id': sim_stock_move.procurement_id.id or False,
                                 'is_over_picking': True})
                    # _logger.warning(u"charlie_0712_log_3:split_move_qty:%s,", split_move)
                    sim_stock_move.production_id.move_raw_ids = sim_stock_move.production_id.move_raw_ids + split_move
                    # _logger.warning(u"charlie_0712_log_4:len_move_raw_ids:%d,",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                    split_move.write({'state': 'assigned', })
                    sim_stock_move.stock_moves[0].quantity_done = sim_stock_move.stock_moves[0].product_uom_qty
                    # _logger.warning(u"charlie_0712_log_5:len_move_raw_ids:%d,",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                    split_move.action_done()
                    # _logger.warning(u"charlie_0712_log_6:len_move_raw_ids:%d,",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                    sim_stock_move.stock_moves[0].action_done()
                    split_move.authorized_stock_move(employee_id, uid)
                    sim_stock_move.stock_moves[0].authorized_stock_move(employee_id, uid)
                    # _logger.warning(u"charlie_0712_log_7:len_move_raw_ids:%d,",
                    #                 len(sim_stock_move.production_id.move_raw_ids))
                else:
                    # _logger.warning(u"charlie_0712_log_8:move_qty:%s,uom_qty:%s", str(move['quantity_ready']),
                    #                 str(sim_stock_move.stock_moves[0].product_uom_qty))
                    if sim_stock_move.stock_moves:
                        true_list = []
                        for move1 in sim_stock_move.stock_moves:
                            if move1.state in ["cancel", "done"]:
                                true_list.append(True)
                            else:
                                true_list.append(False)
                                #     states = sim_stock_move.stock_moves.mapped("state")
                                #     if states in ["cancel", "done"]:
                        logging.warning("charlie0910-2-------%d,%d" % (move['quantity_ready'], all(true_list)))
                        if all(true_list):
                            split_move = sim_stock_move.stock_moves[0].copy(
                                default={'quantity_done': move['quantity_ready'],
                                         'product_uom_qty': move['quantity_ready'],
                                         'production_id': sim_stock_move.production_id.id,
                                         'raw_material_production_id': sim_stock_move.raw_material_production_id.id,
                                         'procurement_id': sim_stock_move.procurement_id.id or False,
                                         'is_over_picking': True})
                            split_move.action_confirm()
                            sim_stock_move.production_id.move_raw_ids = sim_stock_move.production_id.move_raw_ids + split_move
                            split_move.write({'state': 'assigned', })
                            split_move.action_done()
                            split_move.authorized_stock_move(employee_id, uid)
                        else:
                            simss_stock_moves = sim_stock_move.stock_moves.filtered(
                                lambda x: x.state not in ["cancel", "done"])
                            if simss_stock_moves and simss_stock_moves[0]:
                                # sim_stock_move.stock_moves[0].quantity_done_store = move['quantity_ready']
                                if simss_stock_moves[0].state == 'draft':
                                    simss_stock_moves[0].action_confirm()
                                simss_stock_moves[0].quantity_done = move['quantity_ready']
                                simss_stock_moves[0].action_done()
                                simss_stock_moves[0].authorized_stock_move(employee_id, uid)
                            else:
                                split_move = sim_stock_move.stock_moves[0].copy(
                                    default={'quantity_done': move['quantity_ready'],
                                             'product_uom_qty': move['quantity_ready'],
                                             'production_id': sim_stock_move.production_id.id,
                                             'raw_material_production_id': sim_stock_move.raw_material_production_id.id,
                                             'procurement_id': sim_stock_move.procurement_id.id or False,
                                             'is_over_picking': True})
                                split_move.action_confirm()
                                sim_stock_move.production_id.move_raw_ids = sim_stock_move.production_id.move_raw_ids + split_move
                                split_move.write({'state': 'assigned', })
                                split_move.action_done()
                                split_move.authorized_stock_move(employee_id, uid)

                                # _logger.warning(u"charlie_0712_log_9:len_move_raw_ids:%d",
                                #                 len(sim_stock_move.production_id.move_raw_ids))
                sim_stock_move.quantity_ready = 0  # 清0
                sim_stock_move.quantity_done = sim_stock_move.quantity_done + move['quantity_ready']
                # try:
                #     mrp_production.post_inventory()
                # except UserError, e:.filtered(lambda x: x.product_type != 'semi-finished')
                #     return JsonResponse.send_response(STATUS_CODE_ERROR,
                #                                       res_data={"error":e.name})
                # if all(sim_move.is_prepare_finished for sim_move in
                #        stock_move_lines.filtered(lambda x: x.product_type != 'semi-finished')):
                #     mrp_production.write(
                #             {'state': 'finish_prepare_material'})
                #
                #     JPushExtend.send_notification_push(audience=jpush.audience(
                #             jpush.tag(LinklovingAppApi.get_jpush_tags("produce"))
                #     ), notification=mrp_production.product_id.name,
                #             body=_("Qty:%d,Finish picking！") % (mrp_production.product_qty))
        except Exception, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": e.name})
        # _logger.warning(u"charlie_0712_log10:finish, mo:%s", LinklovingAppApi.model_convert_to_dict(order_id, request))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

        ######### 工程领料 接口  ###############

    # 根据领料类型 抓取全部数据
    @http.route('/linkloving_app_api/get_all_material_request_show/', auth='user', type='json', csrf=False)
    def get_all_material_request_show(self, **kwargs):

        picking_type = request.jsonrequest.get("picking_type")
        domain = [('picking_type', '=', picking_type), ('picking_state', 'in', ('approved_finish', 'finish_pick'))]
        material_request_list = request.env["material.request"].sudo().search(domain)

        json_list = {'waiting_data': [],
                     'finish_data': [], }
        for material_one in material_request_list:
            data = {
                'id': material_one.id,
                'name': material_one.name,
                'create_date': material_one.my_create_date,
                'delivery_date': material_one.delivery_date,
                'create_uid': material_one.my_create_uid.name,
                'picking_state': material_one.picking_state,
            }

            if material_one.picking_state == 'approved_finish':
                json_list['waiting_data'].append(data)
            elif material_one.picking_state == 'finish_pick':
                json_list['finish_data'].append(data)

        print('length =%d' % len(material_request_list))

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    @http.route('/linkloving_app_api/get_one_material_request_show', type='json', auth='none', csrf=False, cors='*')
    def get_one_material_request_show(self, **kw):

        material_id = request.jsonrequest.get('material_id')  # 领料单id

        material = request.env['material.request'].sudo().browse(material_id)

        # stock_quant = request.env["stock.quant"].sudo()   quantity_available

        json_list = {
            'create_uid': material.my_create_uid.name,
            'create_date': material.my_create_date,
            'delivery_date': material.delivery_date,
            "picking_cause": material.picking_cause,
            "remark": material.remark,
            'line_ids': [{
                'id': lines.id,
                'qty_product': lines.qty_available,
                'name': lines.product_id.display_name,
                'location': lines.product_id.area_id.name,
                'quantity_available': lines.quantity_available,
                'quantity_done': lines.quantity_done,
                'product_qty': lines.product_qty,
                'reserve': lines.reserve_qty,
            } for lines in material.line_ids],
        }

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    @http.route('/linkloving_app_api/change_material_request_state/', type='json', auth='none', csrf=False, cors='*')
    def change_material_request_state(self, **kw):

        material_id = request.jsonrequest.get('material_id')  # 领料单id

        pack_operation_product_ids = request.jsonrequest.get('pack_operation_product_ids')  # 修改

        if not pack_operation_product_ids:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={'error': _(u"没有订单行")})

        for material_line_one in pack_operation_product_ids:
            lin_ids_one = request.env['material.request.line'].sudo().search([('id', '=', material_line_one.get('id'))])
            lin_ids_one.write({'quantity_done': material_line_one.get('quantity_done')})

        material = request.env['material.request'].sudo().browse(material_id)
        material.btn_click_product_out()

        json_list = [{"state": 'ok'}]

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    @http.route('/linkloving_app_api/get_secondary_mos', type='json', auth='none', csrf=False, cors='*')
    def get_secondary_mos(self, **kw):
        # order_id = request.jsonrequest.get('material_id')
        domain = [("is_secondary_produce", '=', True)]
        mos = request.env["mrp.production"].sudo().search(domain).filtered(lambda x: x.state not in ['cancel', 'done'])

        data = []
        for production in mos:
            data.append(self.get_simple_production_json(production))
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    @http.route('/auto_mrp/partners', type='http', auth="public")
    def partners(self, **kw):
        partner_id = 3
        if partner_id:
            partner_sudo = request.env['res.partner'].sudo().browse(partner_id)
            is_website_publisher = request.env['res.users'].has_group('website.group_website_publisher')
            if partner_sudo.exists():
                values = {
                    'main_object': partner_sudo,
                    'partner': partner_sudo,
                    'edit_page': False
                }
        # return request.render("website_partner.partner_page", values)
        print("12312312312")
        return request.render("linkloving_app_api.listing", {
            'objects': partner_sudo,
        })

    ##修改产品重量
    @http.route('/linkloving_app_api/change_product_weight', type='json', auth='none', csrf=False)
    def change_product_weight(self, **kw):
        product_id = request.jsonrequest.get('product_id')
        weight = request.jsonrequest.get('weight')
        product_json = request.env['product.template'].sudo(LinklovingAppApi.CURRENT_USER()).browse(product_id)
        product_json.write({'weight': weight})
        result_json = LinklovingAppApi.product_template_obj_to_json(product_json)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=result_json)

    @http.route('/linkloving_app_api/get_stock_picking_by_remark', type='json', auth='none', csrf=False)
    def get_stock_picking_by_remark(self, **kw):
        remark = request.jsonrequest.get("remark")
        purchase_orders = request.env["purchase.order"].sudo(LinklovingAppApi.CURRENT_USER()).search(
            [('remark', 'ilike', remark)])
        json_list = []
        for purchase_order in purchase_orders:
            for ids in purchase_order.picking_ids:
                # print purchase_order
                json_list.append(LinklovingAppApi.stock_picking_to_json(ids))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 根据name获取客户信息
    @http.route('/linkloving_app_api/get_one_demo_partner1', type='http', auth="none", csrf=False, cors='*')
    def get_one_demo_partner(self, **kw):

        print kw
        if not kw.get('name'):
            return JsonResponse.send_response(1, res_data={'result': 'erro'}, jsonRequest=False)

        request.session.authenticate(u'Robotime 10_1', 'peter.wang@robotime.com', '123456')
        # request.session.authenticate(u'20170714', 'peter.wang@robotime.com', '123456')

        # request.params["db"] = u'20170714'
        # request.session.db = u'20170714'

        partner_one = http.request.env["res.partner"].search(
            [('name', '=', kw.get('name')), ('customer', '=', True), ('is_company', '=', True)])

        vals = {'result': 'erro'}

        if partner_one:
            if len(partner_one.ids) > 1:
                partner_one = partner_one[0]

            messages_data = series_data = ''
            if partner_one.message_ids:
                messages_data = [
                    {'body': msg.body, 'message_label_ids': [label.name for label in msg.messages_label_ids]} for msg in
                    partner_one.message_ids]

            if partner_one.product_series_ids:
                series_data = [series.name for series in partner_one.product_series_ids]

            vals = {
                'crm_source_id': partner_one.crm_source_id.name if partner_one.crm_source_id else '',  # 来源
                'customer_status': partner_one.customer_status.name if partner_one.customer_status else '',  # 客户状态
                'comment': partner_one.comment if partner_one.comment else '',  # 备注
                'product_series_ids': series_data,  # 感兴趣系列
                'messages_ids': messages_data,  # 感兴趣系列
                'source_id': partner_one.source_id.name if partner_one.source_id else '',  # 渠道

            }

        return JsonResponse.send_response(1, res_data=vals, jsonRequest=False)

    @http.route('/linkloving_app_api/get_account_data', type='json', auth="none", csrf=False, cors='*')
    def get_account_data(self, **kw):
        cash_type = request.env.ref('account.data_account_type_liquidity')

        def _today():
            return (datetime.date.today() + datetime.timedelta(days=0)).strftime('%Y-%m-%d %H:%M:%S')

        accounts = request.env['account.move.line'].sudo().read_group(
            [('user_type_id', '=', cash_type.id), ('create_date', '>', _today())],
            ['account_id', 'credit', 'debit', 'balance', 'date'],
            ['account_id'])
        account_list = []
        credit_all = debit_all = balance_all = month_begin_all = last_day_balance_all = 0.0
        acoount_dict = {}
        for account in accounts:
            res = {
                'credit': account['credit'],
                'debit': account['debit'],
            }
            acoount_dict.update({
                account['account_id'][0]: res
            })

        account_datas = request.env['account.account'].sudo().search(
            [('user_type_id', '=', cash_type.id), ('deprecated', '=', False)])
        for account in account_datas:
            if acoount_dict.get(account.id):
                debit = acoount_dict[account.id].get('debit')
                credit = acoount_dict[account.id].get('credit')
            else:
                debit = 0
                credit = 0
            balance = account.balance
            month_begin = account.month_begin_balance
            last_day_balance = credit - debit + balance

            res = {
                'month_begin': month_begin,
                'name': account.name,
                'debit': debit,
                'credit': credit,
                'balance': balance,
                'last_day_balance': last_day_balance
            }
            account_list.append(res)
            credit_all += credit
            debit_all += debit
            balance_all += balance
            last_day_balance_all += last_day_balance
            month_begin_all += month_begin
        jason_list = {
            'month_begin': month_begin_all,
            # 期初
            'last_day_balance_all': last_day_balance_all,
            # 支出
            'credit_all': credit_all,
            # 收入
            'debit_all': debit_all,
            # 期末
            'balance_all': balance_all,
            'account_list': account_list
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=jason_list)

    @http.route('/linkloving_app_api/get_products', type='json', auth="none", csrf=False, cors='*')
    def get_products(self):
        product_name = request.jsonrequest.get("product_name")
        # db = 'diy0102'
        # request.session.db = db  # 设置账套
        # request.params["db"] = db
        domain = []
        if product_name:
            domain.append(('name', 'ilike', product_name), ('active', '!=', None))
        products = request.env['product.product'].sudo().search(domain,
                                                                limit=10)
        json_list = []
        for p in products:
            res = {
                'id': p.id,
                'name': p.name
            }
            json_list.append(res)
        code = STATUS_CODE_OK

        return JsonResponse.send_response(code, res_data=json_list)

    @http.route('/linkloving_app_api/get_invoice_data', type='json', auth="none", csrf=False, cors='*')
    def get_invoice_data(self):
        invoice_number = request.jsonrequest.get("invoice_number")
        origin = request.jsonrequest.get("origin")
        amount = request.jsonrequest.get("amount")
        # db = 'diy0102'
        # request.session.db = db  # 设置账套
        # request.params["db"] = db

        domain = []
        if invoice_number:
            domain.append(('move_name', 'ilike', invoice_number))
        if origin:
            domain.append(('origin', 'ilike', origin))
        if amount:
            domain.append(('amount_total', '=', amount))
        # d
        invoices = request.env['account.invoice'].sudo().search(domain,
                                                                limit=20)
        json_list = []
        for invoice in invoices:
            data = {
                'customer': invoice.partner_id.name,
                'user_id': invoice.user_id.name,
                'origin': invoice.origin,
                'amount_total': invoice.amount_total,
                'amount_tax': invoice.amount_tax,
                'amount_untaxed': invoice.amount_untaxed,
                'state': invoice.state,
                'number': invoice.number,
                'type': invoice.type,
                'team_id': invoice.team_id.name,
                'line_ids': invoice.parse_invoice_line_data()
            }
            json_list.append(data)
        code = STATUS_CODE_OK

        return JsonResponse.send_response(code, res_data=json_list)

    # 获取备料列表(小幸福改的)
    @http.route('/linkloving_app_api/get_new_mrp_production', type='json', auth='none', csrf=False)
    def get_new_mrp_production(self, **kw):
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        date_to_show = request.jsonrequest.get("date")
        process_id = request.jsonrequest.get("process_id")
        one_days_after = datetime.timedelta(days=1)
        today_time, timez = LinklovingAppApi.get_today_time_and_tz()
        today_time = fields.datetime.strptime(fields.datetime.strftime(today_time, '%Y-%m-%d'),
                                              '%Y-%m-%d')
        # locations = request.env["stock.location"].sudo().get_semi_finished_location_by_user(request.context.get("uid"))

        if date_to_show not in ["delay", "all"]:
            today_time = fields.datetime.strptime(date_to_show, '%Y-%m-%d')

        one_millisec_before = datetime.timedelta(milliseconds=1)  #
        today_time = today_time - one_millisec_before  # 今天的最后一秒
        after_day = today_time + one_days_after
        # location_cir = request.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
        # location_domain = locations.ids + location_cir
        if not process_id:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "未找到工序id"})

        if date_to_show == "delay":
            domain = [('date_planned_start', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S'))]

        elif date_to_show == 'all':
            domain = []

        else:
            domain = [
                ('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
            ]

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if 'production_line_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('production_line_id'):
                domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
            else:
                domain.append(('production_line_id', '=', False))

        if 'origin_sale_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('origin_sale_id'):
                domain.append(('origin_sale_id', '=', request.jsonrequest['origin_sale_id']))
            else:
                domain.append(('origin_sale_id', '=', False))

        if request.jsonrequest.get('state'):
            if request.jsonrequest.get('state') in ('waiting_material', 'prepare_material_ing'):
                domain.append(('state', 'in', ['waiting_material', 'prepare_material_ing']))
            elif request.jsonrequest.get('state') == 'progress':
                domain.append(('feedback_on_rework', '=', None))
                domain.append(('state', '=', 'progress'))
                domain.append(("is_secondary_produce", '=', False))
            else:
                domain.append(('state', '=', request.jsonrequest['state']))

        orders_today = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain
                                                                                                  # ,limit=limit,
                                                                                                  # offset=offset
                                                                                                  )

        data = []
        for production in orders_today:
            data.append(self.get_simple_production_json(production))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 根据产品名称搜索
    @http.route('/linkloving_app_api/get_search_mrp_production', type='json', auth='none', csrf=False)
    def get_search_mrp_production(self, **kw):
        process_id = request.jsonrequest.get("process_id")
        searchText = request.jsonrequest.get("searchText")
        type = request.jsonrequest.get("type")

        if not process_id:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "未找到工序id"})

        domain = []
        if type == 1:
            domain.append(('product_id', 'ilike', searchText))
        elif type == 2:
            domain.append(('name', 'ilike', searchText))

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if 'production_line_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('production_line_id'):
                domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
            else:
                domain.append(('production_line_id', '=', False))

        if request.jsonrequest.get('state'):
            if request.jsonrequest.get('state') in ('waiting_material', 'prepare_material_ing'):
                domain.append(('state', 'in', ['waiting_material', 'prepare_material_ing']))
            elif request.jsonrequest.get('state') == 'progress':
                domain.append(('feedback_on_rework', '=', None))
                domain.append(('state', '=', 'progress'))
                domain.append(("is_secondary_produce", '=', False))
            elif request.jsonrequest.get('state') == 'is_secondary_produce':
                domain.append(("is_secondary_produce", '=', True))
                domain.append(('state', 'not in', ['done', 'cancel']))
            else:
                domain.append(('state', '=', request.jsonrequest['state']))

        orders_today = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).search(domain)

        data = []
        for production in orders_today:
            data.append(self.get_simple_production_json(production))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    @http.route('/linkloving_app_api/account_hk', type='json', auth="none", csrf=False, cors='*')
    def account_hk(self, **kw):
        account = request.env.ref('linkloving_account_inherit.account_hk')
        if account:
            jason_list = account.sudo().json_data()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=jason_list)

    # 返工中()
    @http.route('/linkloving_app_api/get_new_reworking_production', type='json', auth='none', csrf=False)
    def get_new_reworking_production(self):
        partner_id = request.jsonrequest.get('partner_id')
        mrp_production = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER())
        domain = []
        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))
        domain.append(('state', '=', 'progress'))
        domain.append(('feedback_on_rework', '!=', None))

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if 'origin_sale_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('origin_sale_id'):
                domain.append(('origin_sale_id', '=', request.jsonrequest['origin_sale_id']))
            else:
                domain.append(('origin_sale_id', '=', False))

        if 'production_line_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('production_line_id'):
                domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
            else:
                domain.append(('production_line_id', '=', False))

        production_rework = mrp_production.search(domain,
                                                  offset=request.jsonrequest['offset'],
                                                  limit=request.jsonrequest['limit'],
                                                  order='date_planned_start desc'
                                                  )

        data = []
        for production in production_rework:
            data.append(self.get_simple_production_json(production))
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取生产入库品检单
    @http.route('/linkloving_app_api/get_new_qc_feedback', type='json', auth='none', csrf=False)
    def get_new_qc_feedback(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        partner_id = request.jsonrequest.get('partner_id')
        state = request.jsonrequest.get('state')
        is_group_by = request.jsonrequest.get('is_group_by')
        # mrp_production = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER())
        domain = []

        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if 'production_line_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('production_line_id'):
                domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
            else:
                domain.append(('production_line_id', '=', False))

        if is_group_by:
            mos = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).search(domain)
            feedbacks = request.env["mrp.qc.feedback"].sudo(LinklovingAppApi.CURRENT_USER()).search(
                [("state", '=', state), ("production_id", "in", mos.ids)],
                limit=limit,
                offset=offset,
                order='production_id desc')
            group_list = {}
            for feed in feedbacks:
                group_feed = group_list.get(feed.production_id.origin_sale_id.name)
                if group_feed:
                    group_feed.get("feedbacks").append(self.convert_qc_feedback_to_json(feed))
                else:
                    group_list[feed.production_id.origin_sale_id.name or ''] = {
                        'sale_id': feed.production_id.origin_sale_id.id or -1,
                        'feedbacks': [self.convert_qc_feedback_to_json(feed)]
                    }

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.transferJson(group_list))

    # json转化
    def transferJson(self, group_list):
        so_list = []
        for i in range(len(group_list)):
            key = group_list.keys()[i]
            timestamp = group_list[key]['feedbacks']
            streamArr = group_list[key]['sale_id']
            so = {
                'soname': key,
                'feedback': timestamp,
                'sale_id': streamArr
            }
            so_list.append(so)
        return so_list

    # 二次生产增加工序产线分类
    @http.route('/linkloving_app_api/get_secondary_mos', type='json', auth='none', csrf=False, cors='*')
    def get_secondary_mos(self, **kw):
        # order_id = request.jsonrequest.get('material_id')
        domain = [("is_secondary_produce", '=', True)]

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if 'production_line_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('production_line_id'):
                domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
            else:
                domain.append(('production_line_id', '=', False))

        mos = request.env["mrp.production"].sudo().search(domain).filtered(lambda x: x.state not in ['cancel', 'done'])

        data = []
        for production in mos:
            data.append(self.get_simple_production_json(production))
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取so源
    @http.route('/linkloving_app_api/get_so_mrp_production', type='json', auth='none', csrf=False)
    def get_so_mrp_production(self, **kw):
        # limit = request.jsonrequest.get('limit')
        # offset = request.jsonrequest.get('offset')
        process_id = request.jsonrequest.get("process_id")
        is_group_by = request.jsonrequest.get("is_group_by")
        partner_id = request.jsonrequest.get('partner_id')

        domain = []

        if not process_id:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "未找到工序id"})

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if 'production_line_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('production_line_id'):
                domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
            else:
                domain.append(('production_line_id', '=', False))

        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))

        new_domain = None
        if request.jsonrequest.get('state'):
            if request.jsonrequest.get('state') in ('waiting_material', 'prepare_material_ing'):
                domain.append(('state', 'in', ['waiting_material', 'prepare_material_ing']))
            elif request.jsonrequest.get('state') == 'progress':
                domain.append(('feedback_on_rework', '=', None))
                domain.append(('state', '=', 'progress'))
                domain.append(("is_secondary_produce", '=', False))
                new_domain = copy.deepcopy(domain)

                domain.append(("has_produced_product", "=", True))
                new_domain.append(("has_produced_product", "=", False))
            elif request.jsonrequest.get('state') == 'is_secondary_produce':
                domain.append(("is_secondary_produce", '=', True))
                domain.append(('state', 'not in', ['done', 'cancel']))
            elif request.jsonrequest.get('state') == 'rework_ing':
                domain.append(('state', '=', 'progress'))
                domain.append(('feedback_on_rework', '!=', None))
            else:
                domain.append(("is_secondary_produce", '=', False))
                domain.append(('state', '=', request.jsonrequest['state']))

        if is_group_by:
            new_group_by = []
            group_by = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(domain=domain,
                                                                                                      fields=[
                                                                                                          'origin_sale_id'],
                                                                                                      groupby=[
                                                                                                          'origin_sale_id'])
            if new_domain:
                new_group_by = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                    domain=new_domain,
                    fields=[
                        'origin_sale_id'],
                    groupby=[
                        'origin_sale_id'])

        data = []
        # 不隐藏
        for production in group_by:
            data.append(self.get_so_production(production, have=True))
        # 隐藏
        for new_production in new_group_by:
            data.append(self.get_so_production(new_production, have=False))

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    def get_so_production(self, production, have):
        return {
            'origin_id': production.get('origin_sale_id')[0] if production.get('origin_sale_id') else 0,
            'origin_name': production.get('origin_sale_id')[1] if production.get('origin_sale_id') else '',
            'origin_count': production.get('origin_sale_id_count'),
            'have': have,
        }

    # 获取生产状态的数目
    @http.route('/linkloving_app_api/get_count_mrp_production', type='json', auth='none', csrf=False)
    def get_count_mrp_production(self, **kw):
        process_id = request.jsonrequest.get("process_id")
        if not process_id:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "未找到工序id"})
        partner_id = request.jsonrequest.get('partner_id')
        states = request.jsonrequest.get('state')

        group_by = []
        for state in states:
            bean_list = []
            domain = []
            if request.jsonrequest.get('process_id'):
                domain.append(('process_id', '=', request.jsonrequest['process_id']))

            if 'production_line_id' in request.jsonrequest.keys():
                if request.jsonrequest.get('production_line_id'):
                    domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
                else:
                    domain.append(('production_line_id', '=', False))
            if state in ('waiting_material', 'prepare_material_ing'):
                domain.append(('state', 'in', ['waiting_material', 'prepare_material_ing']))
                bean_list = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                    domain=domain,
                    fields=[
                        'origin_sale_id'],
                    groupby=[
                        'origin_sale_id'])
                int_list = []
                for group in bean_list:
                    int_list.append(group.get('origin_sale_id_count'))
                bean = {
                    'state': state,
                    'state_count': sum(int_list)
                }
                group_by.append(bean)
            elif state == 'progress':
                domain.append(('feedback_on_rework', '=', None))
                domain.append(('state', '=', 'progress'))
                domain.append('|')
                domain.append(('in_charge_id', '=', partner_id))
                domain.append(('create_uid', '=', partner_id))
                domain.append(("is_secondary_produce", '=', False))
                bean_list = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                    domain=domain,
                    fields=[
                        'origin_sale_id'],
                    groupby=[
                        'origin_sale_id'])
                int_list = []
                for group in bean_list:
                    int_list.append(group.get('origin_sale_id_count'))
                bean = {
                    'state': state,
                    'state_count': sum(int_list)
                }
                group_by.append(bean)
            elif state == 'is_secondary_produce':
                domain.append('|')
                domain.append(('in_charge_id', '=', partner_id))
                domain.append(('create_uid', '=', partner_id))
                domain.append(("is_secondary_produce", '=', True))
                domain.append(('state', 'not in', ['cancel', 'done']))
                bean_list = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                    domain=domain,
                    fields=[
                        'origin_sale_id'],
                    groupby=[
                        'origin_sale_id'])
                int_list = []
                for group in bean_list:
                    int_list.append(group.get('origin_sale_id_count'))
                bean = {
                    'state': state,
                    'state_count': sum(int_list)
                }
                group_by.append(bean)
            elif state == 'rework_ing':
                domain.append(('state', '=', 'progress'))
                domain.append(('feedback_on_rework', '!=', None))
                bean_list = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                    domain=domain,
                    fields=[
                        'origin_sale_id'],
                    groupby=[
                        'origin_sale_id'])
                int_list = []
                for group in bean_list:
                    int_list.append(group.get('origin_sale_id_count'))
                bean = {
                    'state': state,
                    'state_count': sum(int_list)
                }
                group_by.append(bean)
            elif state == 'already_picking':
                domain.append(('state', '=', state))
                domain.append('|')
                domain.append(('in_charge_id', '=', partner_id))
                domain.append(('create_uid', '=', partner_id))
                bean_list = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                    domain=domain,
                    fields=[
                        'origin_sale_id'],
                    groupby=[
                        'origin_sale_id'])
                int_list = []
                for group in bean_list:
                    int_list.append(group.get('origin_sale_id_count'))
                bean = {
                    'state': state,
                    'state_count': sum(int_list)
                }
                group_by.append(bean)
            elif state in ('waiting_warehouse_inspection', 'force_cancel_waiting_warehouse_inspection'):
                domain.append(("is_secondary_produce", '=', False))
                domain.append(('state', '=', state))
                bean_list = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                    domain=domain,
                    fields=[
                        'origin_sale_id'],
                    groupby=[
                        'origin_sale_id'])
                int_list = []
                for group in bean_list:
                    int_list.append(group.get('origin_sale_id_count'))
                bean = {
                    'state': state,
                    'state_count': sum(int_list)
                }
                group_by.append(bean)
            elif state in ('waiting_inventory_material', 'force_cancel_waiting_return'):
                domain.append(("is_secondary_produce", '=', False))
                domain.append('|')
                domain.append(('in_charge_id', '=', partner_id))
                domain.append(('create_uid', '=', partner_id))
                domain.append(('state', '=', state))
                bean_list = request.env['mrp.production'].sudo(LinklovingAppApi.CURRENT_USER()).read_group(
                    domain=domain,
                    fields=[
                        'origin_sale_id'],
                    groupby=[
                        'origin_sale_id'])
                int_list = []
                for group in bean_list:
                    int_list.append(group.get('origin_sale_id_count'))
                bean = {
                    'state': state,
                    'state_count': sum(int_list)
                }
                group_by.append(bean)

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=group_by)

    # 处理下json格式（邹邹）
    def getJsonCount(self, production):
        return {
            'state': production.get('state'),
            'state_count': production.get('state_count')
        }

    # 二次生产单据修改
    @http.route('/linkloving_app_api/get_new_secondary_mos', type='json', auth='none', csrf=False, cors='*')
    def get_new_secondary_mos(self, **kw):
        process_id = request.jsonrequest.get("process_id")
        partner_id = request.jsonrequest.get('partner_id')

        domain = []
        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))

        if not process_id:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "未找到工序id"})

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if 'production_line_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('production_line_id'):
                domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
            else:
                domain.append(('production_line_id', '=', False))

        if 'origin_sale_id' in request.jsonrequest.keys():
            if request.jsonrequest.get('origin_sale_id'):
                domain.append(('origin_sale_id', '=', request.jsonrequest['origin_sale_id']))
            else:
                domain.append(('origin_sale_id', '=', False))

        domain.append(("is_secondary_produce", '=', True))
        mos = request.env["mrp.production"].sudo().search(domain).filtered(lambda x: x.state not in ['cancel', 'done'])

        data = []
        for production in mos:
            data.append(self.get_simple_production_json(production))
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # start--------------模块:工单---------------分割线--------------------------------------------------start

    # 获取所有标签
    @http.route('/linkloving_app_api/get_all_tags', type='json', auth="none", csrf=False, cors='*')
    def get_all_tags(self, *kw):
        get_all_tags = request.env['linkloving.work.order.tag'].sudo().search([])
        data = {
            "all_tags": self.get_tag_to_json(get_all_tags),
        }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 创建工单
    @http.route('/linkloving_app_api/create_work_order', type='json', auth="none", csrf=False, cors='*')
    def create_work_order(self):
        name = request.jsonrequest.get("title")
        description = request.jsonrequest.get("description")
        priority = request.jsonrequest.get("priority")
        assign_uid = request.jsonrequest.get("assign_uid")
        wo_images = request.jsonrequest.get('wo_images')  # 图片
        departments = request.jsonrequest.get('departments')  # 谁可以看
        category_ids = request.jsonrequest.get('category_ids')
        brand_ids = request.jsonrequest.get('brand_ids')
        area_ids = request.jsonrequest.get('area_ids')

        if not departments:
            departments = request.env['hr.department'].sudo().search([]).ids
        print departments
        issue_state = 'unaccept'
        if assign_uid:
            issue_state = 'process'
        work_order_model = request.env['linkloving.work.order']
        work_order = work_order_model.sudo(LinklovingAppApi.CURRENT_USER()).create({
            'name': name,
            'description': description,
            'priority': priority,
            'assign_uid': assign_uid,
            'issue_state': issue_state,
            'effective_department_ids': [(6, 0, departments)],
            'category_ids': [(6, 0, category_ids)],
            'brand_ids': [(6, 0, brand_ids)],
            'area_ids': [(6, 0, area_ids)],
        })
        if assign_uid:
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(LinklovingAppApi.CURRENT_USER()).create({
                'work_order_id': work_order.id,
                'record_type': "assign",
                'reply_uid': assign_uid,
                'content': "新建并指派受理人：",
            })
        else:
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(LinklovingAppApi.CURRENT_USER()).create({
                'work_order_id': work_order.id,
                'record_type': "assign",
                'content': "新建工单",
            })

        if wo_images:
            for img in wo_images:
                wo_img_id = request.env["linkloving.work.order.image"].sudo(LinklovingAppApi.CURRENT_USER()).create({
                    'work_order_id': work_order.id,
                    'work_order_image': img,
                })
                work_order.attachments = [(4, wo_img_id.id)]

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.convert_work_order_to_json(work_order))

    # "我的"工单统计
    @http.route('/linkloving_app_api/my_work_order_statistics', type='json', auth="none", csrf=False, cors='*')
    def my_work_order_statistics(self, **kw):
        uid = request.jsonrequest.get("uid")
        user = request.env["res.users"].sudo().browse(uid)
        work_order_model = request.env['linkloving.work.order']
        domain = [('assign_uid', '=', uid), (
            'effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)]
        work_order_data = work_order_model.sudo().read_group(domain,
                                                             'issue_state',
                                                             'issue_state')
        result = dict((data['issue_state'], data['issue_state_count']) for data in work_order_data)

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=result)

    # "工单池"工单统计
    @http.route('/linkloving_app_api/work_order_statistics', type='json', auth="none", csrf=False, cors='*')
    def work_order_statistics(self, **kw):
        uid = request.jsonrequest.get("uid")
        user = request.env["res.users"].sudo().browse(uid)
        domain = []
        start_date = request.jsonrequest.get("start_date")
        end_date = request.jsonrequest.get("end_date")
        brand_ids = request.jsonrequest.get("brand_ids")
        area_ids = request.jsonrequest.get("area_ids")
        category_ids = request.jsonrequest.get("category_ids")
        if start_date and end_date:
            timez = fields.datetime.now(pytz.timezone(user.tz)).tzinfo._utcoffset
            begin = fields.datetime.strptime(start_date, '%Y-%m-%d')
            end = fields.datetime.strptime(end_date, '%Y-%m-%d')
            work_order_model = request.env['linkloving.work.order']
            statics_domain = [('create_date', '<', (end - timez).strftime('%Y-%m-%d %H:%M:%S')),
                              ('create_date', '>', (begin - timez).strftime('%Y-%m-%d %H:%M:%S')),
                              ('issue_state', 'in', ['unaccept', 'check', 'process', 'done']),
                              ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)]
            if brand_ids:
                statics_domain += [('brand_ids', 'in', brand_ids)]
            if area_ids:
                statics_domain += [('area_ids', 'in', area_ids)]
            if category_ids:
                statics_domain += [('category_ids', 'in', category_ids)]
            work_order_data = work_order_model.sudo().read_group(
                statics_domain,
                ['issue_state'],
                ['issue_state'])

        else:
            work_order_model = request.env['linkloving.work.order']
            statics_domain = [('issue_state', 'in', ['unaccept', 'check', 'process', 'done']),
                              ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)
                              ]
            if brand_ids:
                statics_domain += [('brand_ids', 'in', brand_ids)]
            if area_ids:
                statics_domain += [('area_ids', 'in', area_ids)]
            if category_ids:
                statics_domain += [('category_ids', 'in', category_ids)]
            work_order_data = work_order_model.sudo().read_group(
                statics_domain, ['issue_state'],
                ['issue_state'])

        print work_order_data
        result = dict((data['issue_state'], data['issue_state_count']) for data in work_order_data)

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=result)

    # "工单池"工单统计1
    @http.route('/linkloving_app_api/work_order_statistics_search', type='json', auth="none", csrf=False, cors='*')
    def work_order_statistics_search(self, **kw):
        uid = request.jsonrequest.get("uid")
        user = request.env["res.users"].sudo().browse(uid)
        domain = []
        start_date = request.jsonrequest.get("start_date")
        end_date = request.jsonrequest.get("end_date")
        tag_ids = request.jsonrequest.get("tag_ids")
        search_type = request.jsonrequest.get("search_type")
        search_text = request.jsonrequest.get("search_text")
        if search_type:
            domain += [(search_type, 'ilike', search_text)]
        if start_date and end_date:
            timez = fields.datetime.now(pytz.timezone(user.tz)).tzinfo._utcoffset
            begin = fields.datetime.strptime(start_date, '%Y-%m-%d')
            end = fields.datetime.strptime(end_date, '%Y-%m-%d')
            work_order_model = request.env['linkloving.work.order']
            if not tag_ids or len(tag_ids) == 0:
                domain += [('create_date', '<', (end - timez).strftime('%Y-%m-%d %H:%M:%S')),
                           ('create_date', '>', (begin - timez).strftime('%Y-%m-%d %H:%M:%S')),
                           ('issue_state', 'in', ['unaccept', 'check', 'process', 'done']),
                           ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)]
                work_order_data = work_order_model.sudo().read_group(domain
                                                                     ,
                                                                     ['issue_state'],
                                                                     ['issue_state'])
            else:
                domain += [('create_date', '<', (end - timez).strftime('%Y-%m-%d %H:%M:%S')),
                           ('create_date', '>', (begin - timez).strftime('%Y-%m-%d %H:%M:%S')),
                           ('issue_state', 'in', ['unaccept', 'check', 'process', 'done']),
                           ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids),
                           ('tag_ids', 'in', tag_ids)]
                work_order_data = work_order_model.sudo().read_group(
                    domain,
                    ['issue_state'],
                    ['issue_state'])

        else:
            work_order_model = request.env['linkloving.work.order']
            if len(tag_ids) == 0:
                domain += [('issue_state', 'in', ['unaccept', 'check', 'process', 'done']),
                           ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)
                           ]
                work_order_data = work_order_model.sudo().read_group(
                    domain, ['issue_state'],
                    ['issue_state'])
            else:
                domain += [('issue_state', 'in', ['unaccept', 'check', 'process', 'done']),
                           ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids),
                           ('tag_ids', 'in', tag_ids)]
                work_order_data = work_order_model.sudo().read_group(
                    domain, ['issue_state'],
                    ['issue_state'])

        print work_order_data
        result = dict((data['issue_state'], data['issue_state_count']) for data in work_order_data)

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=result)

    # "工单池"查询-时间
    @http.route('/linkloving_app_api/work_order_search', type='json', auth="none", csrf=False, cors='*')
    def work_order_search(self, **kw):
        uid = request.jsonrequest.get("uid")
        user = request.env["res.users"].sudo().browse(uid)
        domain = []

        start_date = request.jsonrequest.get("start_date")
        end_date = request.jsonrequest.get("end_date")
        issue_state = request.jsonrequest.get("issue_state")
        create_uid = request.jsonrequest.get("create_uid")
        assign_uid = request.jsonrequest.get("assign_uid")
        work_order_number = request.jsonrequest.get("work_order_number")
        isSearchRecord = request.jsonrequest.get("isSearchOrder")
        brand_ids = request.jsonrequest.get("brand_ids")
        area_ids = request.jsonrequest.get("area_ids")
        category_ids = request.jsonrequest.get("category_ids")
        reply_uid = request.jsonrequest.get("reply_uid")
        record_type = request.jsonrequest.get("record_type")
        search_text = request.jsonrequest.get('search_text')
        search_type = request.jsonrequest.get('search_type')
        contantDraft = request.jsonrequest.get('contantDraft')
        if not contantDraft and not isSearchRecord:
            domain += [('issue_state', '!=', "draft")]
        if start_date and end_date:
            timez = fields.datetime.now(pytz.timezone(user.tz)).tzinfo._utcoffset
            begin = fields.datetime.strptime(start_date, '%Y-%m-%d')
            end = fields.datetime.strptime(end_date, '%Y-%m-%d')
            domain += [
                ('create_date', '<', (end - timez).strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '>', (begin - timez).strftime('%Y-%m-%d %H:%M:%S'))
            ]
        if issue_state:
            domain += [('issue_state', '=', issue_state)]
        if create_uid:
            domain += [('create_uid', '=', create_uid)]
        if assign_uid:
            domain += [('assign_uid', '=', assign_uid)]
        if work_order_number:
            domain += [('order_number', '=', work_order_number)]
        if brand_ids:
            domain += [('brand_ids', 'in', brand_ids)]
        if area_ids:
            domain += [('area_ids', 'in', area_ids)]
        if category_ids:
            domain += [('category_ids', 'in', category_ids)]
        if reply_uid:
            domain += [('reply_uid', '=', reply_uid)]
        if record_type:
            domain += [('record_type', '=', record_type)]
        if search_type:
            domain += [(search_type, 'ilike', search_text)]

        work_order_json = []
        word_order_list = []
        if isSearchRecord:
            work_orders = request.env['linkloving.work.order.record'].sudo().search(
                domain, order='create_date desc')
            for order in work_orders:
                word_order_list.append(order.work_order_id)
            ids = list(set(word_order_list))
            ids.sort(key=word_order_list.index)
            for id in ids:
                if contantDraft:
                    work_order_json.append(LinklovingAppApi.convert_work_order_to_json(id))
                elif id.issue_state != 'draft':
                    work_order_json.append(LinklovingAppApi.convert_work_order_to_json(id))

        else:
            if not create_uid:
                domain += [('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)]
            work_orders = request.env['linkloving.work.order'].sudo().search(
                domain, order='write_date desc')
            for order in work_orders:
                work_order_json.append(LinklovingAppApi.convert_work_order_to_json(order))

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=work_order_json)

    # 查询@ 我的
    @http.route('/linkloving_app_api/searchAtMe', type='json', auth="none", csrf=False, cors='*')
    def searchAtMe(self, **kw):
        uid = request.jsonrequest.get("uid")
        isNumber = request.jsonrequest.get("isNumber")
        domain = []
        domain += [('record_type', 'in', ['reply', 'assign'])]
        if isNumber:
            domain += [('isRead', '=', False)]
        domain += [('reply_uid', '=', uid)]
        work_order_json = []
        work_orders = request.env['linkloving.work.order.record'].sudo().search(
            domain, order='write_date desc')
        for order in work_orders:
            if order.work_order_id.issue_state == "draft":
                continue
            work_order_json.append(LinklovingAppApi.convert_at_me_order_to_json(order))
            if not isNumber:
                order.write({'isRead': True})
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=work_order_json)

    @staticmethod
    def convert_at_me_order_to_json(work_order):
        data = ({
            'at_me_time': work_order.create_date,
            'isRead': work_order.isRead,
            'at_me_type': work_order.record_type,
            'at_me_create_user': LinklovingAppApi.get_user_json(work_order.create_uid.user_ids.id),
            "at_me_description": work_order.content or "",
            'work_order_number': work_order.work_order_id.order_number,
            'work_order_id': work_order.work_order_id.id,
            'title': work_order.work_order_id.name,
            'description': work_order.work_order_id.description,
            'priority': work_order.work_order_id.priority,
            'assign_user': LinklovingAppApi.get_user_json(work_order.work_order_id.assign_uid.id),
            'issue_state': work_order.work_order_id.issue_state,
            'create_user': LinklovingAppApi.get_user_json(work_order.work_order_id.write_uid.id),
            'create_time': work_order.work_order_id.create_date,
            'work_order_images': LinklovingAppApi.get_work_order_img_url(work_order.work_order_id.attachments.ids),
            'effective_department_ids': LinklovingAppApi.get_department_json(
                work_order.work_order_id.effective_department_ids),
            # 'tag_ids': LinklovingAppApi.get_tag_to_json(work_order.work_order_id.tag_ids)
        })
        return data

    # "工单详情"
    @http.route('/linkloving_app_api/work_order_search_by_id', type='json', auth="none", csrf=False, cors='*')
    def work_order_deltail(self, **kw):
        uid = request.jsonrequest.get("uid")
        work_order_id = request.jsonrequest.get("work_order_id")
        user = request.env['res.users'].sudo().browse(uid)

        work_order = request.env['linkloving.work.order'].sudo().search(
            [('id', '=', work_order_id),
             # ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)
             ])
        if work_order:
            work_order_records = request.env['linkloving.work.order.record'].sudo().search(
                [('work_order_id', '=', work_order_id), ('parent_id', '=', False)], order='create_date desc')
            work_order_records1 = request.env['linkloving.work.order.record'].sudo().search(
                [('work_order_id', '=', work_order_id)], order='create_date desc')
            record_json = []
            for record in work_order_records1:
                if uid == record.work_order_id.assign_uid.id:
                    record.write({"isRead": True})  # 标记成已读
            for record in work_order_records:
                record_json.append(LinklovingAppApi.convert_work_order_record_to_json(record))
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data={"work_order": self.convert_work_order_to_json(work_order),
                                                        "records": record_json})
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "work_order_id不存在或无权限访问"})

    # "工单详情 - 操作记录"
    @http.route('/linkloving_app_api/work_order_add_record', type='json', auth="none", csrf=False, cors='*')
    def work_order_add_record(self, **kw):
        content = request.jsonrequest.get("content")
        reply_uid = request.jsonrequest.get("reply_uid")
        record_type = request.jsonrequest.get("record_type")
        work_order_id = request.jsonrequest.get("work_order_id")
        parent_id = request.jsonrequest.get("parent_id")
        uid = request.jsonrequest.get("uid")
        record_imgs = request.jsonrequest.get("record_imgs")
        work_order = request.env['linkloving.work.order'].sudo(uid).browse(work_order_id)

        work_order_record_model = request.env['linkloving.work.order.record']
        work_order_record = work_order_record_model.sudo(uid).create({
            'work_order_id': work_order_id,
            'record_type': record_type,
            'content': content,
            'reply_uid': reply_uid,
            'parent_id': parent_id,
        })

        if record_imgs:
            for img in record_imgs:
                record_img_id = request.env["linkloving.work.order.record.image"].sudo(uid).create({
                    'work_order_record_id': work_order_record.id,
                    'work_order_record_image': img,
                })
                work_order_record.attachments = [(4, record_img_id.id)]
        work_order.sudo(work_order.create_uid.id).write({
            "issue_state": work_order.issue_state
        })
        if work_order_record:
            return JsonResponse.send_response(STATUS_CODE_OK)
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "操作失败"})

    # "工单详情 - 撤回"
    @http.route('/linkloving_app_api/work_order_retract', type='json', auth="none", csrf=False, cors='*')
    def work_order_retract(self, **kw):
        uid = request.jsonrequest.get("uid")
        work_order_id = request.jsonrequest.get("work_order_id")
        need_unlink = request.jsonrequest.get("need_unlink")

        if need_unlink:
            request.env['linkloving.work.order'].sudo(uid).search([
                ('id', '=', work_order_id)
            ]).unlink()

            return JsonResponse.send_response(STATUS_CODE_OK)
        else:
            request.env['linkloving.work.order'].sudo(uid).search([
                ('id', '=', work_order_id), ('write_uid', '=', uid)
            ]).write({
                'issue_state': "draft",
                'assign_uid': False,
            })
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(uid).create({
                'work_order_id': work_order_id,
                'record_type': "draft",
                'content': "撤回单据"
            })

            return JsonResponse.send_response(STATUS_CODE_OK)

    # 工单操作
    @http.route('/linkloving_app_api/work_order_action', type='json', auth="none", csrf=False, cors='*')
    def work_order_action(self, **kw):
        uid = request.jsonrequest.get("uid")
        work_order_id = request.jsonrequest.get("work_order_id")
        action_type = request.jsonrequest.get("action_type")
        assign_uid = request.jsonrequest.get("assign_uid")
        user = request.env['res.users'].sudo().browse(uid)
        if action_type == "assign":
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(uid).create({
                'work_order_id': work_order_id,
                'record_type': "assign",
                'reply_uid': assign_uid,
                'content': "指派受理人："
            })
            work_order = request.env['linkloving.work.order'].sudo().search(
                [('id', '=', work_order_id),
                 ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)])
            work_order.sudo(work_order.create_uid.id).write({
                'assign_uid': assign_uid,
                'issue_state': "process",
            })
            JPushExtend.send_notification_push(audience=jpush.audience(
                jpush.alias(assign_uid)
            ), notification="有新的工单待处理",
                body=_("【工单】%s给你指派了工单：%s") % (user.name, work_order.name))
            return JsonResponse.send_response(STATUS_CODE_OK)
        elif action_type == "check":
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(uid).create({
                'work_order_id': work_order_id,
                'record_type': "check",
                'reply_uid': assign_uid,
            })
            work_order = request.env['linkloving.work.order'].sudo(assign_uid).search(
                [('id', '=', work_order_id),
                 ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)])
            work_order.sudo(assign_uid).write({
                'issue_state': "check",
            })
            return JsonResponse.send_response(STATUS_CODE_OK)
        elif action_type == "reject":
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(uid).create({
                'work_order_id': work_order_id,
                'record_type': "reject",
                'reply_uid': assign_uid,
            })
            work_order = request.env['linkloving.work.order'].sudo(uid).search(
                [('id', '=', work_order_id),
                 ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)])
            work_order.sudo(uid).write({
                'issue_state': "process",
            })
            return JsonResponse.send_response(STATUS_CODE_OK)
        elif action_type == "finish":
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(uid).create({
                'work_order_id': work_order_id,
                'record_type': "finish",
                'reply_uid': assign_uid,
            })
            work_order = request.env['linkloving.work.order'].sudo(uid).search(
                [('id', '=', work_order_id),
                 ('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids)])
            work_order.sudo(uid).write({
                'issue_state': "done",
            })
            return JsonResponse.send_response(STATUS_CODE_OK)

    # 提交草稿状态
    @http.route('/linkloving_app_api/commit_draft', type='json', auth="none", csrf=False, cors='*')
    def commit_draft(self):
        name = request.jsonrequest.get("title")
        description = request.jsonrequest.get("description")
        priority = request.jsonrequest.get("priority")
        assign_uid = request.jsonrequest.get("assign_uid")
        wo_images = request.jsonrequest.get('wo_images')  # 图片
        departments = request.jsonrequest.get('departments')  # 谁可以看
        work_order_id = request.jsonrequest.get('work_order_id')
        # tags = request.jsonrequest.get('tags')
        brand_ids = request.jsonrequest.get('brand_ids')
        area_ids = request.jsonrequest.get('area_ids')
        category_ids = request.jsonrequest.get('category_ids')
        if not departments:
            departments = request.env['hr.department'].sudo().search([]).ids
        print departments
        issue_state = 'unaccept'
        if assign_uid:
            issue_state = 'process'
        work_order_model = request.env['linkloving.work.order']
        work_order = work_order_model.sudo(LinklovingAppApi.CURRENT_USER()).search([('id', '=', work_order_id)])

        work_order.write({
            'name': name,
            'description': description,
            'priority': priority,
            'assign_uid': assign_uid,
            'issue_state': issue_state,
            'effective_department_ids': [(6, 0, departments)],
            'brand_ids': [(6, 0, brand_ids)],
            'area_ids': [(6, 0, area_ids)],
            'category_ids': [(6, 0, category_ids)],
        })
        request.env.cr.execute("UPDATE linkloving_work_order set create_date=%s WHERE id=%s",
                               (fields.datetime.now(), work_order.id))

        if assign_uid:
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(LinklovingAppApi.CURRENT_USER()).create({
                'work_order_id': work_order.id,
                'record_type': "assign",
                'reply_uid': assign_uid,
                'content': "重新提交工单并指派受理人：",
            })
        else:
            work_order_record_model = request.env['linkloving.work.order.record']
            work_order_record = work_order_record_model.sudo(LinklovingAppApi.CURRENT_USER()).create({
                'work_order_id': work_order.id,
                'record_type': "assign",
                'content': "重新提交工单",
            })

        if wo_images:
            for img in wo_images:
                wo_img_id = request.env["linkloving.work.order.image"].sudo(LinklovingAppApi.CURRENT_USER()).create({
                    'work_order_id': work_order.id,
                    'work_order_image': img,
                })
                work_order.attachments = [(4, wo_img_id.id)]

        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.convert_work_order_to_json(work_order))

    # 搜索工单
    @http.route('/linkloving_app_api/search_gongdan', type='json', auth="none", csrf=False, cors='*')
    def search_gongdan(self):
        search_text = request.jsonrequest.get('search_text')
        search_type = request.jsonrequest.get('search_type')
        uid = request.jsonrequest.get("uid")
        user = request.env["res.users"].sudo().browse(uid)
        work_order = request.env['linkloving.work.order'].sudo(uid).search(
            [('effective_department_ids', 'in', user.employee_ids.mapped('department_id').ids),
             (search_type, 'ilike', search_text)], order='write_date desc')
        data = []
        for order in work_order:
            data.append(LinklovingAppApi.convert_work_order_to_json(order))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    # 获取所有工单标签
    @http.route('/linkloving_app_api/get_all_biaoqian', type='json', auth="none", csrf=False, cors='*')
    def get_all_biaoqian(self):
        # create_biaoqian = request.env['linkloving.work.order.tag'].sudo().create({
        #     "name":"若小贝"
        # })
        brand_list = request.env['product.category.brand'].sudo().search([])
        area_list = request.env['hr.department'].sudo().search([])
        category_list = request.env['product.category'].sudo().search([])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"brand_list": self.get_tag_to_json(brand_list),
                                                                    "area_list": self.get_tag_to_json(area_list),
                                                                    "category_list": self.get_tag_to_json(
                                                                        category_list)})

    # 搜索工单标签
    @http.route('/linkloving_app_api/search_biaoqian', type='json', auth="none", csrf=False, cors='*')
    def search_biaoqian(self):
        search_type = request.jsonrequest.get('search_type')
        search_text = request.jsonrequest.get('search_text')
        if (search_type == 'brand'):
            brand_list = request.env['product.category.brand'].sudo().search([("name", 'ilike', search_text)])
            return JsonResponse.send_response(STATUS_CODE_OK, res_data={"type": "brand",
                                                                        "data": self.get_tag_to_json(brand_list)})
        if (search_type == 'area'):
            area_list = request.env['hr.department'].sudo().search([("name", 'ilike', search_text)])
            return JsonResponse.send_response(STATUS_CODE_OK, res_data={"type": "area",
                                                                        "data": self.get_tag_to_json(area_list)})
        if (search_type == 'category'):
            category_list = request.env['product.category'].sudo().search([("name", 'ilike', search_text)])
            return JsonResponse.send_response(STATUS_CODE_OK, res_data={"type": "category",
                                                                        "data": self.get_tag_to_json(category_list)})

    # 修改工单标签
    @http.route('/linkloving_app_api/update_biaoqian', type='json', auth="none", csrf=False, cors='*')
    def update_biaoqian(self):
        uid = request.jsonrequest.get("uid")
        work_order_id = request.jsonrequest.get('work_order_id')
        area_ids = request.jsonrequest.get('area_ids')
        brand_ids = request.jsonrequest.get('brand_ids')
        category_ids = request.jsonrequest.get('category_ids')
        work_order = request.env['linkloving.work.order'].sudo().search(
            [('id', '=', work_order_id)])
        work_order.sudo(uid).write({
            'category_ids': [(6, 0, category_ids)],
            'area_ids': [(6, 0, area_ids)],
            'brand_ids': [(6, 0, brand_ids)],
        })
        return JsonResponse.send_response(STATUS_CODE_OK)

    @staticmethod
    def convert_work_order_record_to_json(record):
        data = {
            # 'order_number': record.order_number,
            'work_order_id': record.work_order_id.id,
            'record_type': record.record_type,
            'reply_uid': LinklovingAppApi.get_user_json(record.reply_uid.id),
            'content': record.content or '',
            'create_date': record.create_date,
            'record_id': record.id,
            'reply_record_line_ids': LinklovingAppApi.convert_work_order_arr_to_json(record.reply_record_line_ids),
            'create_uid': LinklovingAppApi.get_user_json(record.create_uid.id),
            'record_images': LinklovingAppApi.get_work_order_record_img_url(record.attachments.ids)
        }

        return data

    @staticmethod
    def convert_work_order_to_json(work_order):
        records = request.env['linkloving.work.order.record'].sudo().search(
            [('work_order_id', '=', work_order.id), ('parent_id', '=', False)])
        data = ({
            'work_order_number': work_order.order_number,
            'work_order_id': work_order.id,
            'title': work_order.name,
            'description': work_order.description,
            'priority': work_order.priority,
            'assign_user': LinklovingAppApi.get_user_json(work_order.assign_uid.id),
            'issue_state': work_order.issue_state,
            'create_user': LinklovingAppApi.get_user_json(work_order.write_uid.id),
            'create_time': work_order.create_date,
            'work_order_images': LinklovingAppApi.get_work_order_img_url(work_order.attachments.ids),
            'effective_department_ids': LinklovingAppApi.get_department_json(work_order.effective_department_ids),
            'category_ids': LinklovingAppApi.get_tag_to_json(work_order.category_ids),
            'brand_ids': LinklovingAppApi.get_tag_to_json(work_order.brand_ids),
            'area_ids': LinklovingAppApi.get_tag_to_json(work_order.area_ids),
            'comment_count': len(records)
        })
        return data

    # 获取员工详情
    @http.route('/linkloving_app_api/get_employee_detail', type='json', auth="none", csrf=False, cors='*')
    def get_employee_detail(self, *kw):
        user_id = request.jsonrequest.get("user_id")
        employee = request.env['hr.employee'].sudo().search([("user_id", "=", user_id)])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=self.change_employee_to_json(employee))

    def change_employee_to_json(self, obj_d):
        return {
            'id': obj_d.user_id.id,
            'partner_id': obj_d.address_home_id.id or 0,
            'name': obj_d.name_related,  # 姓名
            'work_phone': obj_d.work_phone or '',  # 办公电话
            'mobile_phone': obj_d.mobile_phone or '',  # 办公手机
            'work_email': obj_d.work_email or '',  # email
            'department_id': self.get_department(obj_d.department_id),  # 部门
            'job_id': self.get_department(obj_d.job_id),  # 工作头衔
            'parent_id': self.get_department(obj_d.parent_id),  # 经理
            'image': self.get_user_img_url(obj_d.id, "hr.employee", "image_medium"),
            # 头像
            'user_id': self.get_department(obj_d.user_id),  # '20171213010740'
        }

    def get_department(self, objs):
        return {
            'name': objs.name or '',
            'id': objs.id or '',
        }

    @classmethod
    def get_user_img_url(cls, id, model, field):
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s&time=%s' % (
            request.httprequest.host_url, str(id), model, field, str(time.mktime(datetime.datetime.now().timetuple())))
        if not url:
            return ''
        return url

    @classmethod
    def get_tag_to_json(self, objs):
        data = []
        for obj in objs:
            data.append({
                'name': obj.name,
                'id': obj.id
            })
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    @classmethod
    def get_work_order_img_url(cls, worker_id, ):
        # DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        imgs = []
        for img_id in worker_id:
            url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
                request.httprequest.host_url, str(img_id), 'linkloving.work.order.image', 'work_order_image')
            imgs.append(url)
        return imgs

    @classmethod
    def get_work_order_record_img_url(cls, worker_id, ):
        # DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        imgs = []
        for img_id in worker_id:
            url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
                request.httprequest.host_url, str(img_id), 'linkloving.work.order.record.image',
                'work_order_record_image')
            imgs.append(url)
        return imgs

    @classmethod
    def convert_work_order_arr_to_json(self, objs):
        data = []
        for obj in objs:
            data.append({
                'work_order_id': obj.work_order_id.id,
                'record_type': obj.record_type,
                'reply_uid': LinklovingAppApi.get_user_json(obj.reply_uid.id),
                'content': obj.content or '',
                'create_date': obj.create_date,
                'record_id': obj.id,
                'create_uid': LinklovingAppApi.get_user_json(obj.create_uid.id),
                'record_images': LinklovingAppApi.get_work_order_record_img_url(obj.attachments.ids)
                # 'reply_record_line_ids': record.reply_record_line_ids,
            })
        return data

    @classmethod
    def get_user_json(cls, uid):
        user = request.env["res.users"].sudo().browse(uid)
        data = {
            'id': user.id,
            'name': user.name or "",
            'user_ava': LinklovingAppApi.get_img_url(user.id, "res.users", "image_medium"),
        }
        return data

    @classmethod
    def get_department_json(self, objs):
        data = []
        for obj in objs:
            data.append(obj.id)
        return data

    # end--------------模块:工单---------------分割线--------------------------------------------------end

    # 根据工序获取产线 邹
    @http.route('/linkloving_app_api/get_new_production_lines', type='json', auth='none', csrf=False)
    def get_new_production_lines(self, **kw):
        # request.session.db = request.jsonrequest["db"]
        # request.params["db"] = request.jsonrequest["db"]

        mrp_production = request.env['mrp.production.line'].sudo()
        partner_id = request.jsonrequest.get('partner_id')
        domain = []
        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))

        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))
        g = mrp_production.search(domain)
        line_list = []
        for gg in g:
            line_list.append(self.transter_json_line(gg))
        no_line = {
            'line_id': -1000,
            'line_name': '未分组'
        }
        line_list.append(no_line)
        # g = mrp_production.read_group(domain, fields=['production_line_id'], groupby="production_line_id")
        print(g)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=line_list)

    def transter_json_line(self, line):
        return {
            'line_id': line.id,
            'line_name': line.name
        }

    # 获取生产入库品检单（邹邹改）
    @http.route('/linkloving_app_api/get_count_qc_feedback', type='json', auth='none', csrf=False)
    def get_count_qc_feedback(self, **kw):
        partner_id = request.jsonrequest.get('partner_id')
        state = request.jsonrequest.get('state')
        is_group_by = request.jsonrequest.get('is_group_by')

        if is_group_by:
            groupList = []
            for statesub in state:
                domain = []
                if request.jsonrequest.get('process_id'):
                    domain.append(('process_id', '=', request.jsonrequest['process_id']))

                if 'production_line_id' in request.jsonrequest.keys():
                    if request.jsonrequest.get('production_line_id'):
                        domain.append(('production_line_id', '=', request.jsonrequest['production_line_id']))
                    else:
                        domain.append(('production_line_id', '=', False))
                if statesub == 'qc_success':
                    pass
                elif statesub == 'qc_fail':
                    domain.append('|')
                    domain.append(('in_charge_id', '=', partner_id))
                    domain.append(('create_uid', '=', partner_id))

                mos = request.env["mrp.production"].sudo(LinklovingAppApi.CURRENT_USER()).search(domain)
                feedbacks = request.env["mrp.qc.feedback"].sudo(LinklovingAppApi.CURRENT_USER()).search(
                    [("state", '=', statesub), ("production_id", "in", mos.ids)], order='production_id desc')
                group_list = {}
                for feed in feedbacks:
                    group_feed = group_list.get(feed.production_id.origin_sale_id.name)
                    if group_feed:
                        group_feed.get("feedbacks").append(self.convert_qc_feedback_to_json(feed))
                    else:
                        group_list[feed.production_id.origin_sale_id.name or ''] = {
                            'sale_id': feed.production_id.origin_sale_id.id or -1,
                            'feedbacks': [self.convert_qc_feedback_to_json(feed)]
                        }
                int_list = []
                for i in range(len(group_list)):
                    key = group_list.keys()[i]
                    timestamp = group_list[key]['feedbacks']
                    int_list.append(len(timestamp))

                bean = {
                    'state': statesub,
                    "state_count": sum(int_list)
                }
                groupList.append(bean)

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=groupList)
