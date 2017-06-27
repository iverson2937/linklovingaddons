# -*- coding: utf-8 -*-
import base64
import json
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


app_key = "6e6ce8723531335ce45edd34"
master_secret = "64ec88028aac4dda6286400e"
_jpush = jpush.JPush(app_key, master_secret)
push = _jpush.create_push()
_jpush.set_logging("DEBUG")

need_sound = "a.caf"
apns_production = False
class JPushExtend:
    @classmethod
    def send_notification_push(cls, platform=jpush.all_, audience=None, notification=None, body='', message=None, apns_production=False):
        push.audience = audience
        ios = jpush.ios(alert={"title":notification,
                                       "body":body,
                                       }, sound=need_sound)
        android = jpush.android(alert={"title":notification,
                                       "body":body,
                                       }, priority=1, style=1)
        push.notification = jpush.notification(ios=ios, android=android)
        push.options = {"apns_production":apns_production,}
        push.platform = platform
        try:
            response = push.send()
        except jpush.common.Unauthorized:
            raise jpush.common.Unauthorized("Unauthorized")
        except jpush.common.APIConnectionException:
            raise jpush.common.APIConnectionException("conn")
        except jpush.common.JPushFailure:
            print ("JPushFailure")
        except:
            print ("Exception")


STATUS_CODE_OK = 1
STATUS_CODE_ERROR = -1

#返回的json 封装
class JsonResponse(object):
    @classmethod
    def send_response(cls, res_code, res_msg='', res_data=None, jsonRequest=True):
        data_dic = {'res_code': res_code,
                    'res_msg': res_msg,}
        if res_data:
            data_dic['res_data'] = res_data
        if jsonRequest:
            return data_dic
        return json.dumps(data_dic)

class LinklovingAppApi(http.Controller):

    odoo10 = None
    #获取数据库列表
    @http.route('/linkloving_app_api/get_db_list',type='http', auth='none')
    def get_db_list(self, **kw):
        return JsonResponse.send_response(STATUS_CODE_OK, res_data= http.db_list(), jsonRequest=False)

    #登录
    @http.route('/linkloving_app_api/login', type='json', auth="none", csrf=False)
    def login(self, **kw):
        request.session.db = request.jsonrequest["db"]
        request.params["db"] = request.jsonrequest["db"]

        request.params['login_success'] = False
        values = request.params.copy()
        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db, request.jsonrequest['login'], request.jsonrequest['password'])
            if uid is not False:
                request.params['login_success'] = True
                cur_user = request.env['res.users'].browse(request.uid)
                values['name'] = cur_user.name
                values['user_id'] = request.uid
                #get group ids
                user = LinklovingAppApi.get_model_by_id(uid, request, 'res.users')
                values['partner_id'] = user.partner_id.id
                group_names = request.env['ir.model.data'].sudo().search_read([('res_id', 'in', user.groups_id.ids),
                                                                               ('model', '=', 'res.groups')],
                                                                              fields=['name'])
                #转换中英文标志位
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

    #获取菜单列表
    @http.route('/linkloving_app_api/get_menu_list', type='http', auth="none", csrf=False)
    def get_menu_list(self, **kw):
        if request.session.uid:
            request.uid = request.session.uid
        # context = LinklovingAppApi.loadMenus()
        menu_data = LinklovingAppApi.loadMenus().get('children')
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=menu_data,jsonRequest=False)

    @classmethod
    def get_app_menu_icon_img_url(cls, id, field):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s&time=%s' % (
            request.httprequest.host_url, str(id), 'ir.ui.menu', field, str(time.mktime(datetime.datetime.now().timetuple())))
        if not url:
            return ''
        return url

    @http.route('/linkloving_app_api/get_rework_ing_production', type='json', auth='none', csrf=False)
    def get_rework_ing_production(self):
        partner_id = request.jsonrequest.get('partner_id')
        mrp_production = request.env['mrp.production'].sudo()
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
            dict = {
                'order_id': production.id,
                'display_name': production.display_name,
                'product_name': production.product_id.display_name,
                'date_planned_start': production.date_planned_start,
                'state': production.state,
                'product_qty': production.product_qty,
                'in_charge_name': production.in_charge_id.name,
                'origin': production.origin,
                'process_id': {
                    'process_id': production.process_id.id,
                    'name': production.process_id.name,
                }
            }
            data.append(dict)
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)
    #获取生产单列表
    @http.route('/linkloving_app_api/get_mrp_production', type='json', auth='none', csrf=False)
    def get_mrp_production(self, **kw):
        condition = request.jsonrequest.get('condition')
        mrp_production = request.env['mrp.production'].sudo()
        partner_id = request.jsonrequest.get('partner_id')
        domain = []
        if partner_id:
            domain.append('|')
            domain.append(('in_charge_id', '=', partner_id))
            domain.append(('create_uid', '=', partner_id))

        if request.jsonrequest.get('state'):
            domain.append(('state','=',request.jsonrequest['state']))
            if request.jsonrequest.get('state') == 'progress':
                domain.append(('feedback_on_rework', '=', None))
        if request.jsonrequest.get('process_id'):
            domain.append(('process_id', '=', request.jsonrequest['process_id']))

        if condition and condition[condition.keys()[0]]:
            domain = (condition.keys()[0], 'like', condition[condition.keys()[0]])

        production_all = mrp_production.search(domain,
                                               offset=request.jsonrequest['offset'],
                                               limit=request.jsonrequest['limit'],
                                               order='date_planned_start desc'
                                               )
        data = []
        for production in production_all:
            dict = {
                'order_id': production.id,
                'display_name': production.display_name,
                'product_name': production.product_id.display_name,
                'date_planned_start': production.date_planned_start,
                'state': production.state,
                'product_qty': production.product_qty,
                'qty_produced': production.qty_unpost,
                'in_charge_name':production.in_charge_id.name,
                'origin': production.origin,
                'process_id' : {
                    'process_id': production.process_id.id,
                    'name' : production.process_id.name,
                }
            }
            data.append(dict)
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    @http.route('/linkloving_app_api/get_process_list', type='json', auth='none', csrf=False)
    def get_process_list(self, **kw):
        process_list = request.env['mrp.process'].sudo().search([])
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
        domain = expression.AND([[('state', '=', 'progress')], domain_uid])
        orders_group_by_process = request.env["mrp.production"].sudo().read_group(domain
                                                                                  , fields=["process_id"],
                                                                                  groupby=["process_id"])
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
        locations = request.env["stock.location"].sudo().get_semi_finished_location_by_user(request.context.get("uid"))
        location_cir = request.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
        location_domain = locations.ids + location_cir
        after_day = today_time + one_days_after
        order_delay = request.env["mrp.production"].sudo().read_group(
                [('date_planned_start', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),

                 ('state', 'in', ['waiting_material', 'prepare_material_ing']),

                 ('process_id', '=', process_id),
                 ('location_ids', 'in', location_domain)]
                , fields=["date_planned_start"],
                groupby=["date_planned_start"])

        domain = [('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                  ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                  ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                  ('process_id', '=', process_id),
                  ('location_ids', 'in', location_domain)]
        today_time = today_time + one_days_after
        after_day = after_day + one_days_after
        domain_tommorrow = [('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                            ('process_id', '=', process_id),
                            ('location_ids', 'in', location_domain)]
        today_time = today_time + one_days_after
        after_day = after_day + one_days_after
        domain_after_day = [('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                            ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                            ('process_id', '=', process_id),
                            ('location_ids', 'in', location_domain)]

        order_today = request.env["mrp.production"].sudo().read_group(domain, fields=["date_planned_start"],
                                                                      groupby=["date_planned_start"])
        order_tomorrow = request.env["mrp.production"].sudo().read_group(domain_tommorrow,
                                                                         fields=["date_planned_start"],
                                                                         groupby=["date_planned_start"])
        order_after = request.env["mrp.production"].sudo().read_group(domain_after_day, fields=["date_planned_start"],
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
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=list)

    # 多个工序 的订单数量
    @http.route('/linkloving_app_api/get_order_count_by_process', type='json', auth='none', csrf=False)
    def get_order_count_by_process(self, **kw):
        process_ids = request.jsonrequest.get("process_ids")
        date_to_show, timez = LinklovingAppApi.get_today_time_and_tz()

        one_days_after = datetime.timedelta(days=1)
        today_time = fields.datetime.strptime(fields.datetime.strftime(date_to_show, '%Y-%m-%d'),
                                              '%Y-%m-%d')  # fields.datetime.strftime(date_to_show, '%Y-%m-%d')
        locations = request.env["stock.location"].sudo().get_semi_finished_location_by_user(request.context.get("uid"))
        location_cir = request.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
        location_domain = locations.ids + location_cir

        after_day = today_time + one_days_after
        after_2_day = after_day + one_days_after
        after_3_day = after_2_day + one_days_after
        process_count_dict = {}
        for process_id in process_ids:
            order_delay = request.env["mrp.production"].sudo().read_group(
                    [('date_planned_start', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),

                     ('state', 'in', ['waiting_material', 'prepare_material_ing']),

                     ('process_id', '=', process_id),
                     ('location_ids', 'in', location_domain)]
                    , fields=["date_planned_start"],
                    groupby=["date_planned_start"])

            domain = [('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                      ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                      ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                      ('process_id', '=', process_id),
                      ('location_ids', 'in', location_domain)]

            domain_tommorrow = [('date_planned_start', '>', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                                ('date_planned_start', '<', (after_2_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                                ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                                ('process_id', '=', process_id),
                                ('location_ids', 'in', location_domain)]
            domain_after_day = [('date_planned_start', '>', (after_2_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                                ('date_planned_start', '<', (after_3_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                                ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                                ('process_id', '=', process_id),
                                ('location_ids', 'in', location_domain)]

            order_today = request.env["mrp.production"].sudo().read_group(domain, fields=["date_planned_start"],
                                                                          groupby=["date_planned_start"])
            order_tomorrow = request.env["mrp.production"].sudo().read_group(domain_tommorrow,
                                                                             fields=["date_planned_start"],
                                                                             groupby=["date_planned_start"])
            order_after = request.env["mrp.production"].sudo().read_group(domain_after_day,
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
        locations = request.env["stock.location"].sudo().get_semi_finished_location_by_user(request.context.get("uid"))

        if date_to_show != "delay":
            today_time = fields.datetime.strptime(date_to_show, '%Y-%m-%d')

        one_millisec_before = datetime.timedelta(milliseconds=1)  #
        today_time = today_time - one_millisec_before  # 今天的最后一秒
        after_day = today_time + one_days_after
        location_cir = request.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
        location_domain = locations.ids + location_cir
        if not process_id:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": "未找到工序id"})

        if date_to_show == "delay":
            domain = [('date_planned_start', '<', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
                      ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                      ('process_id', '=', process_id),
                      ('location_ids', 'in', location_domain)]
        else:
            domain = [
            ('date_planned_start', '>', (today_time - timez).strftime('%Y-%m-%d %H:%M:%S')),
            ('date_planned_start', '<', (after_day - timez).strftime('%Y-%m-%d %H:%M:%S')),
                ('state', 'in', ['waiting_material', 'prepare_material_ing']),
                ('process_id', '=', process_id),
                ('location_ids', 'in', location_domain)]

        orders_today = request.env['mrp.production'].sudo().search(domain, limit=limit, offset=offset)

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
                'product_qty': production.product_qty,
                'in_charge_name': production.in_charge_id.name,
                'origin': production.origin,
                'process_id': {
                    'process_id': production.process_id.id,
                    'name': production.process_id.name,
                }
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
        order_delay = request.env["mrp.production"].sudo().read_group(
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

        order_today = request.env["mrp.production"].sudo().read_group(domain, fields=["picking_material_date"],
                                                                      groupby=["picking_material_date"])
        order_tomorrow = request.env["mrp.production"].sudo().read_group(domain_tommorrow,
                                                                         fields=["picking_material_date"],
                                                                         groupby=["picking_material_date"])
        order_after = request.env["mrp.production"].sudo().read_group(domain_after_day,
                                                                      fields=["picking_material_date"],
                                                                      groupby=["picking_material_date"])

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
        orders_today = request.env['mrp.production'].sudo().search(domain, limit=limit, offset=offset)

        data = []
        for production in orders_today:
            data.append(self.get_simple_production_json(production))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)


    #获取生产单详细内容
    @http.route('/linkloving_app_api/get_order_detail', type='json', auth='none', csrf=False)
    def get_order_detail(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #确认订单
    @http.route('/linkloving_app_api/confirm_order', type='json', auth='none', csrf=False)
    def confirm_order(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        order_type = request.jsonrequest.get('order_type')
        mrp_production_model =request.env['mrp.production']
        mrp_production = mrp_production_model.sudo().search([('id', '=', order_id)])[0]
        mrp_production.write({'state': 'waiting_material',
                              'production_order_type' : order_type})
        qty_wizard = request.env['change.production.qty'].sudo().create({
            'mo_id': mrp_production.id,
            'product_qty': mrp_production.product_qty,
        })
        qty_wizard.change_prod_qty()
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #根据生产单号，查询工人列表
    @http.route('/linkloving_app_api/find_worker_lines', type='json', auth='none', csrf=False)
    def find_worker_lines(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        production = LinklovingAppApi.get_model_by_id(order_id, request,'mrp.production')
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
        free_workers = request.env['hr.employee'].sudo().search([('now_mo_id', 'not in', [order_id]),('is_worker', '=', True)])
        free_worker_json = []
        for worker in free_workers:
            free_worker_json.append(self.get_worker_dict(worker))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=free_worker_json)

    #添加工人
    @http.route('/linkloving_app_api/add_worker', type='json', auth='none', csrf=False)
    def add_worker(self, **kw):
        barcode = request.jsonrequest.get('barcode')
        order_id = request.jsonrequest.get('order_id')
        is_add = request.jsonrequest.get('is_add')
        worker_ids = request.jsonrequest.get('worker_ids')
        domain = []
        if worker_ids and len(worker_ids):
            domain.append(('id', 'in', worker_ids))
        if barcode :
            domain.append(('barcode','=', barcode))
        if  worker_ids is None and barcode is None:
            domain.append(('id', '=', 0))

        domain.append(('is_worker','=', True))
        workers = request.env['hr.employee'].sudo().search(domain)
        if not is_add:#如果只是查询工人信息 - 则直接返回员工信息
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=self.get_worker_dict(workers[0]))
        if not workers:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error":_("The operator not found")})
        else:
            for worker in workers:
                if worker.now_mo_id and worker.now_mo_id.id != order_id:#是否正在另一条产线，就退出那一条
                    working_now = request.env['worker.line'].sudo().search(
                            [('worker_id', '=', worker.id),
                             (
                                                                            'production_id', '=', worker.now_mo_id.id)])
                    working_now.change_worker_state('outline')
                    worker.now_mo_id = None
                elif worker.now_mo_id.id == order_id:#防止重复添加
                    continue
                userd_working_line = request.env['worker.line'].sudo().search(
                    [('worker_id', '=', worker.id), ('production_id', '=', order_id)])
                if userd_working_line:#如果曾在这条贡献干过就继续
                    userd_working_line.change_worker_state('online')
                else:
                    worker_line = request.env['worker.line'].sudo().create({
                        'production_id' : order_id,
                        'worker_id' : worker.id
                    })
                    worker.now_mo_id = order_id
                    worker_line.create_time_line()

            worker_lines = []
            for line in LinklovingAppApi.get_model_by_id(order_id,request,'mrp.production').worker_line_ids:
                worker_lines.append(self.get_worker_line_dict(line))
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=worker_lines)

    def get_worker_dict(self, worker):
        data = {
            'name' : worker.name,
            'worker_id' : worker.id,
            'image' :self.get_worker_url(worker.id),
            'barcode' : worker.barcode,
            'job_name' : worker.job_id.name or '',
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
                'worker_id' : time_l.worker_id.id,
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
            'worker_time_line_ids':worker_time_line_ids_list,
            'line_state': obj.line_state,
            'unit_price' : obj.unit_price,
            'xishu' : obj.xishu,
            'amount_of_money' : obj.amount_of_money,

        }
    #修改工人状态
    @http.route('/linkloving_app_api/change_worker_state', type='json', auth='none', csrf=False)
    def change_worker_state(self, **kw):
        is_all_pending = request.jsonrequest.get('is_all_pending')
        order_id = request.jsonrequest.get('order_id')
        worker_line_id = request.jsonrequest.get('worker_line_id')
        new_state = request.jsonrequest.get('state')
        production_order = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if is_all_pending:#如果是批量暂停
            worker_lines = production_order.worker_line_ids
            # worker_lines = request.env['worker.line'].sudo().search([('id', 'in', worker_line_id)])
            worker_lines.change_worker_state(new_state)
            production_order.is_pending = True
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))
        if not worker_line_id and not is_all_pending: #批量恢复
            worker_lines = production_order.worker_line_ids
            # worker_lines = request.env['worker.line'].sudo().search([('id', 'in', worker_line_id)])
            worker_lines.change_worker_state(new_state)

            production_order.is_pending = False
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

        worker_line = request.env['worker.line'].sudo().search(
                [('id', '=', worker_line_id)])
        worker_line.change_worker_state(new_state)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.get_worker_line_dict(worker_line))

    #取消订单
    @http.route('/linkloving_app_api/cancel_order', type='json', auth='none', csrf=False)
    def cancel_order(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        mrp_production_model = request.env['mrp.production']
        mrp_production = mrp_production_model.sudo().search([('id', '=', order_id)])[0]
        mrp_production.action_cancel()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #更新产品数量
    @http.route('/linkloving_app_api/update_produce', type='json', auth='none', csrf=False)
    def update_produce(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        qty = request.jsonrequest.get('product_qty')
        mrp_production_model = request.env['mrp.production']
        mrp_production = mrp_production_model.sudo().search([('id', '=', order_id)])[0]

        qty_wizard = request.env['change.production.qty'].sudo().create({
            'mo_id': mrp_production.id,
            'product_qty': qty,
        })
        qty_wizard.change_prod_qty()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #准备备料
    @http.route('/linkloving_app_api/prepare_material_ing', type='json', auth='none', csrf=False)
    def prepare_material_ing(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        mrp_production_model = request.env['mrp.production']
        mrp_production = mrp_production_model.sudo().search([('id', '=', order_id)])[0]
        mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write({'state': 'prepare_material_ing'})

        JPushExtend.send_notification_push(audience=jpush.audience(
            jpush.tag(LinklovingAppApi.get_jpush_tags("produce"))
        ),notification=mrp_production.product_id.name,body=_("Qty:%d,Already start picking！") % (mrp_production.product_qty))

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 保存物料数据
    @http.route('/linkloving_app_api/saving_material_data', type='json', auth='none', csrf=False)
    def saving_material_data(self, **kw):
        # order_id = request.jsonrequest.get('order_id') #get paramter
        stock_moves = request.jsonrequest.get('stock_moves')  # get paramter
        for stock_move in stock_moves:
            sim_move_obj = request.env["sim.stock.move"].sudo().browse(
                    stock_move["stock_move_lines_id"])
            sim_move_obj.quantity_ready = stock_move['quantity_ready']
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})
    #备料完成
    @http.route('/linkloving_app_api/finish_prepare_material', type='json', auth='none', csrf=False)
    def finish_prepare_material(self, **kw):
        order_id = request.jsonrequest.get('order_id') #get paramter
        mrp_production = request.env['mrp.production'].sudo().search([('id', '=', order_id)])[0]

        stock_moves = request.jsonrequest.get('stock_moves') #get paramter
        stock_move_lines = request.env["sim.stock.move"].sudo()
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
                    split_move.write({'state': 'assigned',})
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
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #领料登记
    @http.route('/linkloving_app_api/already_picking', type='json', auth='none', csrf=False)
    def already_picking(self, **kw):
        order_id = request.jsonrequest.get('order_id') #get paramter
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
                split_move.write({'state': 'assigned',})
                sim_stock_move.stock_moves[0].quantity_done = sim_stock_move.stock_moves[0].product_uom_qty
                split_move.action_done()
                sim_stock_move.stock_moves[0].action_done()
            else:
                sim_stock_move.stock_moves[0].quantity_done_store = move['quantity_ready']
                sim_stock_move.stock_moves[0].quantity_done = move['quantity_ready']
                sim_stock_move.stock_moves[0].action_done()
            sim_stock_move.quantity_ready = 0  #清0
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
        mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write({'state': 'progress'})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #补领料
    @http.route('/linkloving_app_api/over_picking', type='json', auth='none', csrf=False)
    def over_picking(self, **kw):
        order_id = request.jsonrequest.get('order_id') #get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')

        stock_moves = request.jsonrequest.get('stock_moves') #get paramter
        for l in stock_moves:
            move = LinklovingAppApi.get_model_by_id(l['stock_move_lines_id'], request, 'sim.stock.move')
            if not move:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={'error': _("Stock move not found")})
            if l['over_picking_qty'] != 0:#如果超领数量不等于0
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

    #产出
    @http.route('/linkloving_app_api/do_produce', type='json', auth='none', csrf=False)
    def do_produce(self, **kw):
        order_id = request.jsonrequest.get('order_id') #get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if not mrp_production:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error' : _("The MO not found")})
        produce_qty = request.jsonrequest.get('produce_qty')

        try:
            mrp_product_produce = request.env['mrp.product.produce'].with_context({'active_id': order_id})
            produce = mrp_product_produce.sudo().create({
                'product_qty' : produce_qty,
                'production_id' : order_id,
                'product_uom_id' :mrp_production.product_uom_id.id,
                'product_id' : mrp_production.product_id.id,
            })
            produce.do_produce()
        except Exception, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': e.name})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #送往品检
    @http.route('/linkloving_app_api/produce_finish', type='json', auth='none', csrf=False)
    def produce_finish(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')

        if not mrp_production:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error' : _("The MO not found")})
        if mrp_production.qty_unpost == 0:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error':_("Product qty can not be 0 ")})
        if mrp_production.qty_unpost <= mrp_production.product_qty and mrp_production.production_order_type == 'ordering':
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Ordering MO need to produce all the products")})
        else:
            if mrp_production.feedback_on_rework:  # 生产完成, 但是还在返工中 说明此次返工还没产出
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={"error": u"该单据还在返工中,请先产出数量"})
            # 生产完成 结算工时
            mrp_production.state = mrp_production.compute_order_state()

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
        order = request.env["mrp.production"].sudo().browse(order_id)
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
        order = request.env["mrp.production"].sudo().browse(order_id)
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
    #开始品检
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


    #品检结果
    @http.route('/linkloving_app_api/inspection_result', type='json', auth='none', csrf=False)
    def inspection_result(self, **kw):

        feedback_id = request.jsonrequest.get('feedback_id')  # get paramter
        result = request.jsonrequest.get('result')

        qc_test_qty = request.jsonrequest.get('qc_test_qty')#抽样数量
        qc_fail_qty = request.jsonrequest.get('qc_fail_qty')#不良品数量
        qc_note = request.jsonrequest.get('qc_note')#批注
        qc_img = request.jsonrequest.get('qc_img')#图片
        feedback = LinklovingAppApi.get_model_by_id(feedback_id, request, 'mrp.qc.feedback')
        feedback.write({
            'qc_test_qty' : qc_test_qty,
            'qc_fail_qty' : qc_fail_qty,
            'qc_note' : qc_note,
        })
        for img in qc_img:
            qc_img_id = request.env["qc.feedback.img"].sudo().create({
                'feedback_id': feedback.id,
                'qc_img': img,
            })
            feedback.qc_imgs = [(4, qc_img_id.id)]

        if not feedback:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error' : _("MO not found")})
        try:
            if result == True:
                feedback.sudo().action_qc_success()
            else:
                feedback.sudo().action_qc_fail()
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
            mrp_production.write({'state': 'done'})
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))
        if not is_check:
            try:
                for l in stock_move_ids:
                    product_id = l['product_tmpl_id']
                    obj = request.env['return.material.line'].sudo().create({
                        'return_qty': l['return_qty'],
                        'product_id': product_id,
                    })
                    return_lines.append(obj.id)

                return_material_model = request.env['mrp.return.material']
                returun_material_obj = return_material_model.sudo().search(
                        [('production_id', '=', order_id),
                         ('state', '=', 'draft')])
                if not returun_material_obj:  # 如果没生成过就生成一遍， 防止出现多条记录
                    returun_material_obj = return_material_model.sudo().create({
                        'production_id': mrp_production.id,
                    })

                else:
                    returun_material_obj.production_id = mrp_production.id

                returun_material_obj.return_ids = return_lines
                mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write(
                        {'state': 'waiting_warehouse_inspection'})
            except Exception, e:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={"error": e.name})
        else:
            try:
                return_material_model = request.env['mrp.return.material']
                returun_material_obj = return_material_model.sudo().search(
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
                    move = request.env['stock.move'].sudo().create(
                            returun_material_obj._prepare_move_values(r))
                    move.action_done()
                returun_material_obj.return_ids.create_scraps()
                mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write({'state': 'done'})
            except Exception, e:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={"error": e.name})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))



    #退料
    @http.route('/linkloving_app_api/return_material', type='json', auth='none', csrf=False)
    def return_material(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        stock_move_ids = request.jsonrequest.get('stock_moves')
        is_check = request.jsonrequest.get('is_check')
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if not mrp_production:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error' : _("MO not found")})
        return_lines = []
        if all(stock_move.get("return_qty") == 0 for stock_move in stock_move_ids):
            mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write({'state': 'done'})
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))
        try:
            if not is_check:

                for l in stock_move_ids:
                    product_id = l['product_tmpl_id']
                    obj = request.env['return.material.line'].sudo().create({
                        'return_qty': l['return_qty'],
                        'product_id': product_id,
                    })
                    return_lines.append(obj.id)

                return_material_model = request.env['mrp.return.material']
                returun_material_obj = return_material_model.sudo().search(
                        [('production_id', '=', order_id),
                         ('state', '=', 'draft')])
                if not returun_material_obj:  # 如果没生成过就生成一遍， 防止出现多条记录
                    returun_material_obj = return_material_model.sudo().create({
                        'production_id': mrp_production.id,
                    })

                else:
                    returun_material_obj.production_id = mrp_production.id

                returun_material_obj.return_ids = return_lines
                mrp_production.sudo(request.context.get("uid") or SUPERUSER_ID).write(
                        {'state': 'waiting_warehouse_inspection'})
            else:
                return_material_model = request.env['mrp.return.material']
                returun_material_obj = return_material_model.sudo().search([('production_id', '=', order_id),
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
                    move = request.env['stock.move'].sudo().create(
                            returun_material_obj._prepare_move_values(r))
                    move.action_done()
                returun_material_obj.return_ids.create_scraps()
                mrp_production.write({'state': 'done'})
                #
                # location = request.env["stock.location"].sudo().search([("is_circulate_location", "=", True)], limit=1)
                # if location and location.putaway_strategy_id and location.putaway_strategy_id.fixed_location_ids:
                #     fixed_location_ids = location.putaway_strategy_id.fixed_location_ids
                #
                #     if mrp_production.product_id.categ_id.id in fixed_location_ids.mapped("category_id").ids:  # 半成品入库
                #     else:
                #         mrp_production.write({'state': 'waiting_post_inventory'})
        except Exception, e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": e.name})

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #获得退料单信息
    @http.route('/linkloving_app_api/get_return_detail', type='json', auth='none', csrf=False)
    def get_return_detail(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        return_material_model = request.env['mrp.return.material']
        return_lines = return_material_model.sudo().search_read([('production_id', '=', order_id),
                                                                 ('state', '=', 'draft')], limit=1)
        return_material_obj = return_material_model.sudo().search([('production_id', '=', order_id),
                                                                   ('state', '=', 'draft')])
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
            }
            data.append(dic)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=data)

    @http.route('/linkloving_app_api/get_feedback_detail', type='json', auth='none', csrf=False)
    def get_feedback_detail(self, **kw):
        feedback_id = request.jsonrequest.get('feedback_id')
        feedback = request.env["mrp.qc.feedback"].sudo().browse(feedback_id)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=self.convert_qc_feedback_to_json(feedback))

    @http.route('/linkloving_app_api/get_qc_feedback', type='json', auth='none', csrf=False)
    def get_qc_feedback(self, **kw):
        limit = request.jsonrequest.get("limit")
        offset = request.jsonrequest.get("offset")
        order_id = request.jsonrequest.get('order_id')
        state = request.jsonrequest.get('state')
        if order_id:
            feedbacks = request.env["mrp.production"].sudo().browse(order_id).qc_feedback_ids
        if state:
            feedbacks = request.env["mrp.qc.feedback"].sudo().search([("state", '=', state)],
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
                "order_id": qc_feedback.production_id.id,
                "display_name": qc_feedback.production_id.display_name,
                'product_id': {
                    'product_id': qc_feedback.product_id.id,
                    'product_name': qc_feedback.product_id.name,
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
    #生产完成入库
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

    #根据id 和model  返回对应的实例
    @classmethod
    def get_model_by_id(cls, id, request, model):
        model_obj = request.env[model].sudo().search([('id', '=', id)])
        if model_obj:
            return model_obj[0]
        else:
            return None

    #生产单转换成json
    @classmethod
    def model_convert_to_dict(cls,order_id, request, ):
        mrp_production = request.env['mrp.production'].sudo()
        production = mrp_production.search([('id','=',order_id)], limit=1)

        stock_move = request.env['sim.stock.move'].sudo().search_read([('id', 'in', production.sim_stock_move_lines.ids)],
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
        for l in stock_move:
            # dic = LinklovingAppApi.search(request,'product.product',[('id','=',l['product_id'][0])], ['display_name'])
            if l.get("product_id"):
                l['product_tmpl_id'] = l['product_id'][0] #request.env['product.product'].sudo().search([('id','=',l['product_id'][0])]).id
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
            'product_id': {
                'product_id': production.product_id.id,
                'product_name': production.product_id.display_name,
                'product_ll_type': production.product_id.product_ll_type or '',
                'product_specs': production.product_id.product_specs,
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
            'qty_produced': production.qty_unpost,
            'process_id': {
                'process_id': production.process_id.id,
                'name': production.process_id.name,
                'is_rework': production.process_id.is_rework,
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
            # 'factory_remark': production.factory_remark,
        }
        return data

    @classmethod
    def get_prepare_material_img_url(cls, worker_id, ):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
            request.httprequest.host_url, str(worker_id), 'mrp.production','prepare_material_img')
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
            domain.append((key, 'in', [condition_dic[key]]))
        sudo_model = request.env['product.product'].sudo()
        product_s = sudo_model.search(domain)
        if product_s:
            data = {
                'theoretical_qty': product_s.qty_available,
                'product_qty': 0,
                'product': {
                    'product_id': product_s.id,
                    'product_name': product_s.display_name,
                    'image_medium': LinklovingAppApi.get_product_image_url(product_s, model='product.product'),
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
                                              res_data={'error' : _("Product not found")})
    #获取盘点单列表
    @http.route('/linkloving_app_api/get_stock_inventory_list', type='json', auth='none', csrf=False)
    def get_stock_inventory_list(self, **kw):
        offset = request.jsonrequest.get('offset')
        limit = request.jsonrequest.get('limit')
        list = request.env['stock.inventory'].sudo().search([], order='date desc', offset=offset , limit=limit)
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
        inventory = request.env['stock.inventory'].sudo().search([('id', '=', inventory_id)], limit=1)
        if inventory:
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=LinklovingAppApi.stock_inventory_model_to_dict(inventory[0], is_detail=True))
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error' : _("Order not found")})

        #stock.location.area 处理部分
    #获取仓库位置列表
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

    #所有关于交接信息的处理
    @http.route('/linkloving_app_api/upload_note_info', type='json', auth='none', csrf=False)
    def upload_note_info(self, **kw):
        type = request.jsonrequest.get('type')#交接所处的类型，状态
        order_id = request.jsonrequest.get('order_id') #生产单号
        img = request.jsonrequest.get('img')
        area_name = request.jsonrequest.get('area_name')
        if type == 'prepare_material_ing':
            mrp_order = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
            area = request.env['stock.location.area'].sudo().search(
                    [('name', '=', area_name)])
            if not area:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={'error' : _("Location error!")})
            mrp_order.prepare_material_area_id = area.id
            mrp_order.prepare_material_img = img
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Wrong status")})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})

    #创建盘点单
    @http.route('/linkloving_app_api/create_stock_inventory', type='json', auth='none', csrf=False)
    def create_stock_inventory(self, **kw):
        stock_inventory_lines = request.jsonrequest.get('line_ids')
        name = request.jsonrequest.get('name')
        new_lines = []
        try:
            for line in stock_inventory_lines:
                product_obj = LinklovingAppApi.get_model_by_id(line['product']['product_id'], request,
                                                               'product.product')
                line['product_uom_id'] = product_obj.uom_id.id
                product_obj.area_id = line['product']['area']['area_id']
                if line['product'].get('image_medium'):
                    image_str = line['product'].get('image_medium')
                    print 'image_str:%s' % image_str[0:16]
                    try:
                        product_obj.product_tmpl_id.image_medium = image_str
                    except Exception, e:
                        print "exception catch %s" % image_str[0:16]
                location_id = request.env.ref('stock.stock_location_stock', raise_if_not_found=False).id

                new_line = {
                    'product_id': product_obj.id,
                    'product_uom_id': product_obj.uom_id.id,
                    'location_id': location_id,
                    'product_qty': line['product_qty']
                }
                new_lines.append((0, 0, new_line))
        except:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error": "数据提交异常"})
        try:
            inventory = request.env['stock.inventory'].sudo().create({
                'name': name,
                'filter': 'partial',
                'line_ids': new_lines
            })
            inventory.action_done()
        except UserError,e:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error":e.name})

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})
    @classmethod
    def stock_inventory_model_to_dict(cls, obj, is_detail):
        line_ids = []
        if is_detail:
            line_ids = request.env['stock.inventory.line'].sudo().search_read(
                    [('id', 'in', obj.line_ids.ids)], fields=['product_id',
                                                                                                                        'product_qty',
                                                                                                                        'theoretical_qty',
                                                              ])
            for line in line_ids:
                product_n = request.env['product.product'].sudo().browse(
                        line['product_id'][0])
                area = product_n.area_id
                c = {
                    'id' :  line['product_id'][0] ,
                    'product_name' :  line['product_id'][1],
                    'product_spec': product_n.product_specs,
                    'image_medium': LinklovingAppApi.get_product_image_url(
                            request.env['product.product'].sudo().browse(
                                    line['product_id'][0])[0],
                            model='product.product'),
                    'area' : {
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
            'date' : obj.date,
            'name' : obj.display_name,
            'location_name' : obj.location_id.name,
            'state' : obj.state,
            # 'total_qty' : obj.total_qty,
            'line_ids' : line_ids if line_ids else None
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
        product_id =kw.get('product_id')
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

            content = odoo.tools.image_resize_image(base64_source=content, size=( None, None),
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



    def placeholder(self, image='placeholder.png'):
        addons_path = http.addons_manifest['web']['addons_path']
        return open(os.path.join(addons_path, 'web', 'static', 'src', 'img', image), 'rb').read()


    def force_contenttype(self, headers, contenttype='image/png'):
        dictheaders = dict(headers)
        dictheaders['Content-Type'] = contenttype
        return dictheaders.items()



    #产品模块
    #根据条件查找产品
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
            list = request.env['product.template'].sudo().search(domain, limit=limit, offset=offset)
            for product in list:
                product_json_list.append(LinklovingAppApi.product_template_obj_to_json(product))


        else:
            domain.append(convert_product_type(product_type))
            list = request.env['product.template'].sudo().search(domain, limit=limit, offset=offset)
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
        stock_moves = request.env['stock.move'].sudo().search([('product_tmpl_id', '=', product_id)], limit=limit, offset=offset)
        stock_move_json_list = []
        for stock_move in stock_moves:
            stock_move_json_list.append(LinklovingAppApi.stock_move_obj_to_json(stock_move))
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=stock_move_json_list)


    @classmethod
    def stock_move_obj_to_json(cls, stock_move):
        data = {
            'name' : stock_move.name,
            'product_id' : {
                'product_name' : stock_move.product_tmpl_id.display_name,
                'id' :stock_move.product_tmpl_id.id,
            },
            'product_uom_qty' : stock_move.product_uom_qty,
            'state' : stock_move.state,
            'location': stock_move.location_id.display_name,
            'location_dest' : stock_move.location_dest_id.display_name,
        }
        return data
    @classmethod
    def product_template_obj_to_json(cls, product_tmpl):
        data = {
            'product_id': product_tmpl.id,
            'product_product_id' : product_tmpl.product_variant_id.id,
            'default_code': product_tmpl.default_code,
            'product_name' : product_tmpl.name,
            'type': product_tmpl.type,
            'inner_code': product_tmpl.inner_code,
            'inner_spec': product_tmpl.inner_spec,
            'area_id': {
                'area_name': product_tmpl.area_id.name,
                'area_id': product_tmpl.area_id.id
            },
            'product_spec': product_tmpl.product_specs,
            'image_medium' : LinklovingAppApi.get_product_image_url(product_tmpl, model='product.template'),
            'qty_available' : product_tmpl.qty_available,
            'virtual_available' : product_tmpl.virtual_available,
            'categ_id' : product_tmpl.categ_id.name,
        }
        return data

    @http.route('/linkloving_app_api/get_stock_picking_by_origin', type='json', auth='none', csrf=False)
    def get_stock_picking_by_origin(self, **kw):
        order_name = request.jsonrequest.get("order_name")
        type = request.jsonrequest.get("type")
        if order_name:
            pickings = request.env["stock.picking"].sudo().search([('origin', 'like', order_name),
                                                                   ('picking_type_code', '=', type)])
            json_list = []
            for picking in pickings:
                json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR, res_data={"error": u"请输入单名"})
    #产品出入库部分
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
                group_ret = request.env['stock.picking.type'].sudo().search([('id','=',group_id)], limit=1)
                if group_ret:
                    group_obj = group_ret[0]
                temp_domain = []
                temp_domain.append(('picking_type_id', '=', group_id))
                if partner_id:
                    temp_domain.append(('partner_id', 'child_of', partner_id))

                state_group_list = request.env[model].sudo().read_group(temp_domain, fields=['state'], groupby=['state'])
                new_group = {
                    'picking_type_id' : group_id,
                    'picking_type_name' : group.get('picking_type_id')[1],
                    'picking_type_code' : group_obj.code,
                    'picking_type_id_count' : group.get('picking_type_id_count'),
                    'states' : state_group_list,
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


        request.env["stock.picking"].sudo().search([("state", "in", ("partially_available", "assigned", "confirmed")),
                                                    ("picking_type_code", "=", "outgoing")])._compute_complete_rate()
        group_list = request.env["stock.picking"].sudo().read_group(domain,
                                                                    fields=["complete_rate"],
                                                                    groupby=["complete_rate"])

        group_complete = request.env["stock.picking"].sudo().read_group(domain_complete,
                                                                        fields=["state"],
                                                                        groupby=["state"])
        complete_rate = 99
        complete_rate_count = 0
        new_group = []
        for group in group_list:
            group.pop("__domain")
            if group.get("complete_rate") > 0 and group.get("complete_rate") < 100 or group.get("complete_rate") < 0:
                complete_rate_count += group.get("complete_rate_count")
            else:
                new_group.append(group)

        new_group.append({"complete_rate": complete_rate,
                          "complete_rate_count": complete_rate_count})
        # group_complete[0].pop("__domain")
        group_done = {}
        if group_complete:
            group_done = group_complete[0]
        return JsonResponse.send_response(STATUS_CODE_OK, res_data={"complete_rate": new_group,
                                                                    "state": group_done})

    @http.route('/linkloving_app_api/do_unreserve_action', type='json', auth='none', csrf=False)
    def do_unreserve_action(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        picking = request.env["stock.picking"].sudo().search([("id", "=", picking_id)])
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
            request.env["stock.picking"].sudo().search(domain)._compute_complete_rate()

        picking_list = request.env['stock.picking'].sudo().search(domain,
                                                                  limit=limit,
                                                                  offset=offset,
                                                                  order='name desc')

        json_list = []
        for picking in picking_list:
            json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    #获取stock.PICKING列表
    @http.route('/linkloving_app_api/get_stock_picking_list', type='json', auth='none', csrf=False)
    def get_stock_picking_list(self, **kw):
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        picking_type_id = request.jsonrequest.get('picking_type_id')
        partner_id = request.jsonrequest.get('partner_id')
        state = request.jsonrequest.get("state")
        domain = []
        domain.append(('picking_type_id', '=', picking_type_id))
        domain.append(('state', '=', state))
        if partner_id:
            domain.append(('partner_id', 'child_of', partner_id))

        picking_list = request.env['stock.picking'].sudo().search(domain, limit=limit, offset=offset, order='name desc')
        json_list = []
        for picking in picking_list:
            json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    @http.route('/linkloving_app_api/action_assign_stock_picking', type='json', auth='none', csrf=False)
    def action_assign_stock_picking(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        is_check_all = request.jsonrequest.get("check_all")
        if is_check_all:
            pickings = request.env["stock.picking"].sudo().search(
                    [("state", "in", ["partially_available", "assigned", "confirmed"]),
                     ("picking_type_code", "=", "outgoing")])
            pickings.action_assign()
            return JsonResponse.send_response(STATUS_CODE_OK, res_data={})

        picking = request.env["stock.picking"].sudo().search([("id", "=", picking_id)])
        try:
            picking.action_assign()
        except UserError:
            return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.stock_picking_to_json(picking))

    @http.route('/linkloving_app_api/force_assign', type='json', auth='none', csrf=False)
    def force_assign(self, **kw):
        picking_id = request.jsonrequest.get("picking_id")
        picking = request.env["stock.picking"].sudo().search([("id", "=", picking_id)])
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

    #根据销售还是采购来获取stock.picking 出入库
    @http.route('/linkloving_app_api/get_incoming_outgoing_stock_picking', type='json', auth='none', csrf=False)
    def get_incoming_outgoing_stock_picking(self, **kw):
        limit = request.jsonrequest.get('limit')
        offset = request.jsonrequest.get('offset')
        picking_type_code = request.jsonrequest.get('picking_type_code')
        state = request.jsonrequest.get("state")
        domain = []
        domain.append(('state', '=', state))
        if picking_type_code:
            domain.append(('picking_type_code', '=', picking_type_code))

        picking_list = request.env['stock.picking'].sudo().search(domain, limit=limit, offset=offset, order='name desc')
        json_list = []
        for picking in picking_list:
            json_list.append(LinklovingAppApi.stock_picking_to_json(picking))
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=json_list)

    # 查看bom详情
    @http.route('/linkloving_app_api/get_bom_detail', type='json', auth="none", csrf=False)
    def get_bom_detail(self, **kw):
        order_id = request.jsonrequest.get("order_id")

        order = request.env["mrp.production"].sudo().browse(order_id)

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=order.bom_id.get_bom())

    @http.route('/linkloving_app_api/change_stock_picking_state', type='json', auth='none', csrf=False)
    def change_stock_picking_state(self, **kw):
        state = request.jsonrequest.get('state')  # 状态
        picking_id = request.jsonrequest.get('picking_id')  # 订单id

        pack_operation_product_ids = request.jsonrequest.get('pack_operation_product_ids')  # 修改
        if not pack_operation_product_ids:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': _("Pack Order not found")})

        pack_list = request.env['stock.pack.operation'].sudo().search(
                [('id', 'in', map(lambda a: a['pack_id'], pack_operation_product_ids))])
        # 仓库或者采购修改了数量
        qty_done_map = map(lambda a: a['qty_done'], pack_operation_product_ids)

        def x(a, b):
            a.qty_done = b

        map(x, pack_list, qty_done_map)

        picking_obj = request.env['stock.picking'].sudo().search(
                [('id', '=', picking_id)])
        if state == 'confirm':#确认 标记为代办
            picking_obj.action_confirm()
        elif state == 'post':#提交
            post_img = request.jsonrequest.get('post_img')
            post_area_name = request.jsonrequest.get('post_area_name')
            area = request.env['stock.location.area'].sudo().search([('name', '=',post_area_name)])
            if not area:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={'error': _("Please choose the right location")})
            picking_obj.post_img = post_img
            picking_obj.post_area_id = area[0].id

            picking_obj.action_post()
        elif state == 'cancel':#取消
            picking_obj.action_cancel()
        elif state == 'qc_ok' or state == 'qc_failed':#品检结果
            qc_note = request.jsonrequest.get('qc_note')
            qc_img = request.jsonrequest.get('qc_img')
            picking_obj.qc_note = qc_note
            picking_obj.qc_img = qc_img
            # if state == 'qc_ok':
            picking_obj.action_check_pass()
            # else:
            #     picking_obj.action_check_fail()
        elif state == 'reject':#退回
            picking_obj.reject()
        elif state == 'process':#创建欠单
            ####判断库存是否不够
            if picking_obj.picking_type_code == "outgoing":
                for pack in pack_list:
                    if pack.qty_done > pack.product_id.qty_available:
                        return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                          res_data={
                                                              "error": u"%s 产品库存不足,无法完成出货" % pack.product_id.display_name})

                wiz = request.env['stock.backorder.confirmation'].sudo().create({'pick_id': picking_id})
                is_yes = request.jsonrequest.get("qc_note")  # 货是否齐
                if picking_obj.sale_id:
                    if (picking_obj.sale_id.delivery_rule == "delivery_once" or not picking_obj.sale_id.delivery_rule) \
                            and is_yes != "yes":
                        return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                          res_data={"error": u"该销售单需要一次性发完货,请等待货齐后再发"})
                    elif picking_obj.sale_id.delivery_rule == "delivery_once" and picking_obj.state != "assigned":
                        return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                          res_data={"error": u"该单据为部分可用,请等待货齐后再发"})
                    elif picking_obj.sale_id.delivery_rule == "cancel_backorder":  # 取消欠单
                        wiz.process_cancel_backorder()
                        picking_obj.to_stock()

                    elif picking_obj.sale_id.delivery_rule == "create_backorder":  #创建欠单
                        wiz.process()
                        picking_obj.to_stock()
                    elif picking_obj.sale_id.delivery_rule == "delivery_once" and is_yes == "yes" and picking_obj.state == "assigned":  # 一次性出货并备货完成
                        wiz.process()
                        picking_obj.to_stock()
                else:
                    return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                      res_data={"error": "此单据未关联任何销售单!"})
            elif picking_obj.picking_type_code == "incoming":
                wiz = request.env['stock.backorder.confirmation'].sudo().create({'pick_id': picking_id})
                wiz.process()
        elif state == 'cancel_backorder':  # 取消欠单\
            wiz = request.env['stock.backorder.confirmation'].sudo().create({'pick_id': picking_id})
            wiz.process_cancel_backorder()
        elif state == 'transfer':#入库
            picking_obj.to_stock()
        elif state == 'start_prepare_stock': #开始备货
            picking_obj.start_prepare_stock()
        # elif state == 'stock_ready':#备货完成
        #     picking_obj.stock_ready()
        elif state == 'upload_img':
            express_img = request.jsonrequest.get('qc_img')
            DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
            self.add_file_to_attachment(express_img,
                                        "express_img_%s.png" % time.strftime(DEFAULT_SERVER_DATE_FORMAT,
                                                                             time.localtime()),
                                        "stock.picking", picking_id)
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.stock_picking_to_json(picking_obj))

    def add_file_to_attachment(self, ufile, file_name, model, id):
        Model = request.env['ir.attachment'].sudo()
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
        Model = request.env['ir.attachment'].sudo()
        attach = Model.search([("res_id", "=", res_id),
                               ("res_model", "=", res_model)])
        # http://localhost:8069/web/content/1826?download=true
        if attach:
            return True
        else:
            return False
    @classmethod
    def stock_picking_to_json(cls, stock_picking_obj):
        pack_list = []
        for pack in stock_picking_obj.pack_operation_product_ids:
            pack_list.append({
                'pack_id': pack.id,
                'product_id':{
                    'id': pack.product_id.id,
                    'name': pack.product_id.display_name,
                    'default_code': pack.product_id.default_code,
                    'qty_available': pack.product_id.qty_available,
                    'area_id': {
                        'area_id': pack.product_id.area_id.id or None,
                        'area_name': pack.product_id.area_id.name or None,
                    }
                },
                'product_qty' : pack.product_qty,
                'qty_done' : pack.qty_done,
            })

        data = {
            'picking_id' : stock_picking_obj.id,
            'complete_rate': stock_picking_obj.complete_rate,
            'has_attachment': LinklovingAppApi.is_has_attachment(stock_picking_obj.id, 'stock.picking'),
            'sale_note': stock_picking_obj.sale_id.remark,
            'delivery_rule': stock_picking_obj.delivery_rule or None,
            'picking_type_code' : stock_picking_obj.picking_type_code,
            'name': stock_picking_obj.name,
            'parnter_id': stock_picking_obj.partner_id.display_name,
            'phone': stock_picking_obj.partner_id.mobile or stock_picking_obj.partner_id.phone or '',
            'origin': stock_picking_obj.origin,
            'state': stock_picking_obj.state,
            'min_date': stock_picking_obj.min_date,
            'pack_operation_product_ids': pack_list,
            'qc_note': stock_picking_obj.qc_note,
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
    def get_stock_picking_img_url(cls, picking_id, field):
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s' % (
            request.httprequest.host_url, str(picking_id), 'stock.picking', field)
        if not url:
            return ''
        return url

    #搜索供应商
    @http.route('/linkloving_app_api/search_supplier', type='json', auth='none', csrf=False)
    def search_supplier(self, **kw):
        name = request.jsonrequest.get('name')
        partner_type = request.jsonrequest.get('type') # supplier or customer
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
    def res_partner_to_json(cls, res_partner):
        data = {
            'partner_id': res_partner.id,
            'name' : res_partner.name or '',
            'phone' : res_partner.phone or '',
            'comment' : res_partner.comment or '',
            'x_qq' : res_partner.x_qq or '',
        }
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
            [('res_id', 'in', menus.ids), ('model', '=', 'ir.ui.menu')],fields=['complete_name', 'res_id'])
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
        if type == 'qc':#品检组 tag
            return 'group_charge_inspection'
        elif type == 'warehouse':#仓库组
            return 'group_charge_warehouse'
        elif type == 'produce':#生产组
            return 'group_charge_produce'
        elif type == 'purchase_user':#采购用户
            return 'group_purchase_user'
        elif type == 'purchase_manager':#采购管理员
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

        order = request.env["mrp.production"].sudo().browse(order_id)
        order.factory_remark = remark

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})

    @http.route('/linkloving_app_api/get_factory_remark', type='json', auth='none', csrf=False)
    def get_factory_remark(self, **kw):
        order_id = request.jsonrequest.get("order_id")

        order = request.env["mrp.production"].sudo().browse(order_id)

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={"factory_mark": order.factory_remark or ''})

    @http.route('/linkloving_app_api/create_material_remark', type='json', auth='none', csrf=False)
    def create_material_remark(self, **kw):
        content = request.jsonrequest.get("content")

        remark = request.env["material.remark"].sudo().create({
            "content": content,
        })
        all_remarks = request.env["material.remark"].sudo().search_read([])
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=all_remarks)

    @http.route('/linkloving_app_api/get_material_remark', type='json', auth='none', csrf=False)
    def get_material_remark(self, **kw):
        remarks = request.env["material.remark"].sudo().search_read([])
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=remarks)

    @http.route('/linkloving_app_api/add_material_remark', type='json', auth='none', csrf=False)
    def add_material_remark(self, **kw):
        order_id = request.jsonrequest.get("order_id")
        remark_id = request.jsonrequest.get("remark_id")

        order = request.env["mrp.production"].sudo().browse(order_id)
        order.material_remark_id = remark_id
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})
