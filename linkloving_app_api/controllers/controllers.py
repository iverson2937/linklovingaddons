# -*- coding: utf-8 -*-
import base64
import json
from urllib2 import URLError
import pickle

import time

from pip import download

import odoo
import odoo.modules.registry
from odoo.addons.web.controllers.main import ensure_db

from odoo.api import call_kw, Environment
from odoo.modules import get_resource_path
from odoo.tools import float_compare, SUPERUSER_ID, werkzeug, os
from odoo.tools import topological_sort
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlwt
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, \
                      serialize_exception as _serialize_exception
from odoo.exceptions import AccessError
from odoo.models import check_method_name

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
        ensure_db()
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
                group_names = request.env['ir.model.data'].sudo().search_read([('res_id', 'in', user.groups_id.ids),('model','=','res.groups')], fields=['name'])
                values['groups'] = group_names
                values['login_success'] = True
                return JsonResponse.send_response(STATUS_CODE_OK, res_data=values)
            else:
                request.uid = old_uid
                values['error'] = _("Wrong login/password")
        else:
            values['error'] = _("Wrong Request Method")
        return JsonResponse.send_response(STATUS_CODE_ERROR, res_data=values)

    #获取菜单列表
    @http.route('/linkloving_app_api/get_menu_list', type='http', auth="none", csrf=False)
    def get_menu_list(self, **kw):
        if request.session.uid:
            request.uid = request.session.uid
        context = request.env['ir.http'].sudo().webclient_rendering_context()
        menu_data = context.get('menu_data').get('children')
        for menu in menu_data:
            menu['user_id'] = request.uid
            if menu.get('web_icon_data'):
                menu.pop('web_icon_data')
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=menu_data,jsonRequest=False)

    #获取生产单列表
    @http.route('/linkloving_app_api/get_mrp_production', type='json', auth='none', csrf=False)
    def get_mrp_production(self, **kw):
        condition = request.jsonrequest.get('condition')
        mrp_production = request.env['mrp.production'].sudo()
        domain = []
        if request.jsonrequest.get('state'):
            domain = [('state','=',request.jsonrequest['state'])]
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
            'user_id': production.user_id.name,
            'origin': production.origin,
            }
            data.append(dict)
        # user_data = LinklovingAppApi.odoo10.execute('res.users', 'read', [LinklovingAppApi.odoo10.env.user.id])
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=data)

    #获取生产单详细内容
    @http.route('/linkloving_app_api/get_order_detail', type='json', auth='none', csrf=False)
    def get_order_detail(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        mrp_production = request.env['mrp.production'].sudo()
        production = mrp_production.search([('id','=',order_id)], limit=1)

        # stock_move = request.env['sim.stock.move'].sudo().search_read([('id', 'in', production.sim_stock_move_lines.ids)], fields=['product_id', 'over_picking_qty', 'qty_available', 'quantitty_available', 'quantity_done', 'return_qty','virtual_available', 'quantity_ready', 'product_uom_qty', 'suggest_qty'])
        # for l in stock_move:
        #     # dic = LinklovingAppApi.search(request,'product.product',[('id','=',l['product_id'][0])], ['display_name'])
        #     l['product_id'] = request.env['product.product'].sudo().search([('id','=',l['product_id'][0])]).display_name
        # data = {
        #     'order_id' : production.id,
        #     'display_name' : production.display_name,
        #     'product_name' : production.product_id.display_name,
        #     'date_planned_start' : production.date_planned_start,
        #     'bom_name' : production.bom_id.display_name,
        #     'state' : production.state,
        #     'product_qty' : production.product_qty,
        #     'production_order_type' : production.production_order_type,
        #     'user_id' : production.user_id.name,
        #     'origin' : production.origin,
        #     'cur_location': None,
        #     'stock_move_lines' : stock_move,
        # }
        return JsonResponse.send_response(STATUS_CODE_OK, res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #确认订单
    @http.route('/linkloving_app_api/confirm_order', type='json', auth='none', csrf=False)
    def confirm_order(self, **kw):
        order_id = request.jsonrequest.get('order_id')
        order_type = request.jsonrequest.get('order_type')
        mrp_production_model =request.env['mrp.production']
        mrp_production = mrp_production_model.sudo().search([('id','=',order_id)])[0]
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

    #添加工人
    @http.route('/linkloving_app_api/add_worker', type='json', auth='none', csrf=False)
    def add_worker(self, **kw):
        barcode = request.jsonrequest.get('barcode')
        order_id = request.jsonrequest.get('order_id')
        worker = request.env['hr.employee'].sudo().search([('barcode','=', barcode)], limit=1)[0]
        if not worker:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={"error":u"找不到此员工"})
        else:
            worker_line = request.env['worker.line'].sudo().create({
                'production_id' : order_id,
                'worker_id' : worker.id
            })
            return JsonResponse.send_response(STATUS_CODE_OK,
                                              res_data=self.get_worker_line_dict(worker_line))

    def get_worker_line_dict(self, obj):
        return {
            'id': obj.id,
            'worker': {
                'id': obj.worker_id.id,
                'name': obj.worker_id.name
            },
            'join_time': obj.join_time,
            'line_state': obj.line_state,
        }
    #修改工人状态
    @http.route('/linkloving_app_api/change_worker_state', type='json', auth='none', csrf=False)
    def change_worker_state(self, **kw):
        # worker_line_id =
        new_state = request.jsonrequest.get('state')


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
        mrp_production.write({'state': 'prepare_material_ing'})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #备料完成
    @http.route('/linkloving_app_api/finish_prepare_material', type='json', auth='none', csrf=False)
    def finish_prepare_material(self, **kw):
        order_id = request.jsonrequest.get('order_id') #get paramter
        mrp_production_model = request.env['mrp.production']
        mrp_production = mrp_production_model.sudo().search([('id', '=', order_id)])[0]

        stock_moves = request.jsonrequest.get('stock_moves') #get paramter
        stock_move_lines = []
        for move in stock_moves:
            sim_stock_move = LinklovingAppApi.get_model_by_id(move['stock_move_lines_id'], request, 'sim.stock.move')
            rounding = sim_stock_move.stock_moves[0].product_uom.rounding
            if float_compare(move['quantity_ready'], sim_stock_move.stock_moves[0].product_uom_qty, precision_rounding=rounding) > 0:
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
            else:
                sim_stock_move.stock_moves[0].quantity_done = move['quantity_ready']

        mrp_production.post_inventory()
        mrp_production.write({'state': 'finish_prepare_material'})

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #领料登记
    @http.route('/linkloving_app_api/already_picking', type='json', auth='none', csrf=False)
    def already_picking(self, **kw):
        order_id = request.jsonrequest.get('order_id') #get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        mrp_production.write({'state': 'already_picking'})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    # 开始生产
    @http.route('/linkloving_app_api/start_produce', type='json', auth='none', csrf=False)
    def start_produce(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        mrp_production.write({'state': 'progress'})
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
            if l['over_picking_qty'] != 0:#如果超领数量不等于0
                new_move = move.stock_moves[0].copy(default={'quantity_done': l['over_picking_qty'], 'product_uom_qty':  l['over_picking_qty'], 'production_id': move.production_id.id,
                                            'raw_material_production_id': move.raw_material_production_id.id,
                                            'procurement_id': move.procurement_id.id or False,
                                            'is_over_picking': True})
                move.production_id.move_raw_ids =  move.production_id.move_raw_ids + new_move
                move.over_picking_qty = 0
                new_move.write({'state':'assigned',})
        mrp_production.post_inventory()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #产出
    @http.route('/linkloving_app_api/do_produce', type='json', auth='none', csrf=False)
    def do_produce(self, **kw):
        order_id = request.jsonrequest.get('order_id') #get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        produce_qty = request.jsonrequest.get('produce_qty')

        try:
            mrp_product_produce = request.env['mrp.product.produce']
            produce = mrp_product_produce.sudo().create({
                'product_qty' : produce_qty,
                'production_id' : order_id,
                'product_uom_id' :mrp_production.product_uom_id.id,
                'product_id' : mrp_production.product_id.id,
            })
            produce.do_produce()
        except:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error':'do produce error'})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #送往品检
    @http.route('/linkloving_app_api/produce_finish', type='json', auth='none', csrf=False)
    def produce_finish(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')

        if mrp_production.qty_produced == 0:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error':u'您还未产出任何产品，不可做此操作！'})
        if not mrp_production.check_to_done and mrp_production.production_order_type == 'ordering':
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error': u'此生产单为订单制，需要产成所有数量的产品才能送往品检！'})
        else:
            mrp_production.write({'state': 'waiting_quality_inspection'})

        return JsonResponse.send_response(STATUS_CODE_OK,
                                      res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #开始品检
    @http.route('/linkloving_app_api/start_quality_inspection', type='json', auth='none', csrf=False)
    def start_quality_inspection(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        mrp_production.write({'state': 'quality_inspection_ing'})
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #品检结果
    @http.route('/linkloving_app_api/inspection_result', type='json', auth='none', csrf=False)
    def inspection_result(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        result = request.jsonrequest.get('result')
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        if result == True:
            mrp_production.write({'state': 'waiting_inventory_material'})
        else:
            mrp_production.write({'state': 'progress'})

        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #退料
    @http.route('/linkloving_app_api/return_material', type='json', auth='none', csrf=False)
    def return_material(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        stock_move_ids = request.jsonrequest.get('stock_moves')
        is_check = request.jsonrequest.get('is_check')
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        return_lines = []

        if not is_check:

            for l in stock_move_ids:
                product_id = l['product_tmpl_id']
                obj = request.env['return.material.line'].sudo().create({
                    'return_qty': l['return_qty'],
                    'product_id': product_id,
                })
                return_lines.append(obj.id)

            return_material_model = request.env['mrp.return.material']
            returun_material_obj = return_material_model.sudo().search([('production_id','=',order_id)])
            if not returun_material_obj:#如果没生成过就生成一遍， 防止出现多条记录
                returun_material_obj = return_material_model.sudo().create({
                    'production_id' : mrp_production.id,
                })

            else:
                returun_material_obj.production_id = mrp_production.id

            returun_material_obj.return_ids = return_lines
            mrp_production.write({'state': 'waiting_warehouse_inspection'})
        else:
            return_material_model = request.env['mrp.return.material']
            returun_material_obj = return_material_model.sudo().search([('production_id', '=', order_id)])
            if not returun_material_obj:
                return JsonResponse.send_response(STATUS_CODE_ERROR,
                                                  res_data={'error' : u'暂无退料信息'})
            returun_material_obj.state = 'done'
            #退料信息 已经确认
            for r in returun_material_obj.return_ids:
                for new_qty_dic in stock_move_ids:
                    if r.product_id.id == new_qty_dic['product_tmpl_id']:
                        r.return_qty = new_qty_dic['return_qty']
                if r.return_qty == 0:
                    continue
                move = request.env['stock.move'].sudo().create(returun_material_obj._prepare_move_values(r))
                move.action_done()
            mrp_production.write({'state': 'waiting_post_inventory'})

        return JsonResponse.send_response(STATUS_CODE_OK,
                                      res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #获得退料单信息
    @http.route('/linkloving_app_api/get_return_detail', type='json', auth='none', csrf=False)
    def get_return_detail(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        return_material_model = request.env['mrp.return.material']
        return_lines = return_material_model.sudo().search_read([('production_id', '=', order_id)], limit=1)
        return_material_obj = return_material_model.sudo().search([('production_id', '=', order_id)])

        return_lines[0]['product_ids'] = []
        data = []
        for return_line in return_material_obj.return_ids:
            dic = {
                'product_tmpl_id' : return_line.product_id.id,
                'product_id' : return_line.product_id.display_name,
                'return_qty' : return_line.return_qty,
            }
            data.append(dic)
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=data)

    #生产完成入库
    @http.route('/linkloving_app_api/produce_done', type='json', auth='none', csrf=False)
    def produce_done(self, **kw):
        order_id = request.jsonrequest.get('order_id')  # get paramter
        mrp_production = LinklovingAppApi.get_model_by_id(order_id, request, 'mrp.production')
        mrp_production.button_mark_done()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                      res_data=LinklovingAppApi.model_convert_to_dict(order_id, request))

    #根据id 和model  返回对应的实例
    @classmethod
    def get_model_by_id(cls, id, request, model):
        return request.env[model].sudo().search([('id', '=', id)])[0]

    #生产单转换成json
    @classmethod
    def model_convert_to_dict(cls,order_id, request, ):
        mrp_production = request.env['mrp.production'].sudo()
        production = mrp_production.search([('id','=',order_id)], limit=1)

        stock_move = request.env['sim.stock.move'].sudo().search_read([('id', 'in', production.sim_stock_move_lines.ids)],
                                                                      fields=['product_id',
                                                                              'product_tmpl_id',
                                                                              'over_picking_qty',
                                                                              'qty_available',
                                                                              'quantity_available',
                                                                              'quantity_done',
                                                                              'return_qty',
                                                                              'virtual_available',
                                                                              'quantity_ready',
                                                                              'product_uom_qty',
                                                                              'quantity_available',
                                                                              'suggest_qty'])
        for l in stock_move:
            # dic = LinklovingAppApi.search(request,'product.product',[('id','=',l['product_id'][0])], ['display_name'])
            l['product_tmpl_id'] = l['product_id'][0] #request.env['product.product'].sudo().search([('id','=',l['product_id'][0])]).id
            l['product_id'] = l['product_id'][1]
            l['order_id'] = order_id
        data = {
            'order_id' : production.id,
            'display_name' : production.display_name,
            'product_name' : production.product_id.display_name,
            'date_planned_start' : production.date_planned_start,
            'bom_name' : production.bom_id.display_name,
            'state' : production.state,
            'product_qty' : production.product_qty,
            'production_order_type' : production.production_order_type,
            'user_id' : production.user_id.name,
            'origin' : production.origin,
            'cur_location': None,
            'stock_move_lines' : stock_move,
            'qty_produced' : production.qty_produced,
        }
        return data

#盘点接口
    #根据条件查找产品
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
                'theoretical_qty' : product_s.qty_available,
                'product_qty' : 0,
                'product' : {
                    'id' : product_s.id,
                    'product_name' : product_s.name,
                    'image_medium' : LinklovingAppApi.get_product_image_url(product_s),
                    'area' : {
                        'id' : product_s.area_id.id,
                        'name' : product_s.area_id.name,
                    }
                }
            }
            return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=data)
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error' : u'未找到该产品'})
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
                                              res_data={'error' : u'未找到对应的单子',})


    #获取仓库位置列表
    @http.route('/linkloving_app_api/get_area_list', type='json', auth='none', csrf=False)
    def get_area_list(self, **kw):
        areas = request.env['stock.location.area'].sudo().search_read([])

        return JsonResponse.send_response(STATUS_CODE_OK,
                                         res_data=areas)


    #创建盘点单
    @http.route('/linkloving_app_api/create_stock_inventory', type='json', auth='none', csrf=False)
    def create_stock_inventory(self, **kw):
        stock_inventory_lines = request.jsonrequest.get('line_ids')
        name = request.jsonrequest.get('name')
        new_lines = []
        for line in stock_inventory_lines:
            product_obj = LinklovingAppApi.get_model_by_id(line['product']['id'],request,'product.product')
            line['product_uom_id'] = product_obj.uom_id.id
            product_obj.area_id = line['product']['area']['id']
            if line['product'].get('image_medium'):
                image_str = line['product'].get('image_medium')
                print 'image_str:%s' % image_str[0:16]
                try:
                    product_obj.product_tmpl_id.image_medium = image_str
                except Exception, e:
                    print "exception catch %s" % image_str[0:16]
            location_id = request.env.ref('stock.stock_location_stock', raise_if_not_found=False).id

            new_line = {
                'product_id' : product_obj.id,
                'product_uom_id' : product_obj.uom_id.id,
                'location_id' : location_id,
                'product_qty' : line['product_qty']
            }
            new_lines.append((0, 0, new_line))


        inventory = request.env['stock.inventory'].sudo().create({
            'name': name,
            'filter': 'partial',
            'line_ids': new_lines
        })
        inventory.action_done()
        return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data={})
    @classmethod
    def stock_inventory_model_to_dict(cls, obj, is_detail):
        line_ids = []
        if is_detail:
            line_ids = request.env['stock.inventory.line'].sudo().search_read([('id', 'in', obj.line_ids.ids)], fields=['product_id',
                                                                                                                 'product_qty',
                                                                                                                 'theoretical_qty',
                                                                                                                 ])
            for line in line_ids:
                area = request.env['product.product'].sudo().browse(line['product_id'][0]).area_id
                c = {
                    'id' :  line['product_id'][0] ,
                    'product_name' :  line['product_id'][1],
                    'image_medium' : LinklovingAppApi.get_product_image_url(request.env['product.product'].sudo().browse(line['product_id'][0])[0]),
                    'area' : {
                    'id': area.id,
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
    def get_product_image_url(cls, product_product):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        url = request.httprequest.host_url  \
              + 'linkloving_app_api/get_product_image?product_id='+str(product_product.product_tmpl_id.id)
        if not url:
            return ''
        return url


    @http.route('/linkloving_app_api/get_product_image', type='http', auth='none', csrf=False)
    def get_product_image(self, **kw):
        DEFAULT_SERVER_DATE_FORMAT = "%Y%m%d%H%M%S"
        product_id =kw.get('product_id')

        status, headers, content = request.registry['ir.http'].binary_content(xmlid=None, model='product.template', id=product_id, field='image_medium', unique=time.strftime(DEFAULT_SERVER_DATE_FORMAT, time.localtime()),
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
                return ()
            elif type == 'purchase':
                return ('purchase_ok', '=', True)
            elif type == 'sale':
                return ('sale_ok', '=', True)
            elif type == 'expensed':
                return ('can_be_expensed', '=', True)
            else:
                return ()

        if not condition_dic:
            list = request.env['product.template'].sudo().search([convert_product_type(product_type)], limit=limit, offset=offset)

        domain = []
        for key in condition_dic.keys():
            domain.append((key, 'in', [condition_dic[key]]))
        sudo_model = request.env['product.product'].sudo()
        product_s = sudo_model.search(domain)
        if product_s:
            data = {
                'theoretical_qty' : product_s.qty_available,
                'product_qty' : 0,
                'product' : {
                    'id' : product_s.id,
                    'product_name' : product_s.name,
                    'image_medium' : LinklovingAppApi.get_product_image_url(product_s),
                    'area' : {
                        'id' : product_s.area_id.id,
                        'name' : product_s.area_id.name,
                    }
                }
            }
            return JsonResponse.send_response(STATUS_CODE_OK,
                                          res_data=data)
        else:
            return JsonResponse.send_response(STATUS_CODE_ERROR,
                                              res_data={'error' : u'未找到该产品'})


    @classmethod
    def product_template_obj_to_json(cls, product_tmpl):
        data = {
            'product_id': product_tmpl.id,
            'default_code': product_tmpl.default_code,
            'type': product_tmpl.type,
            'inner_code': product_tmpl.inner_code,
            'inner_spec': product_tmpl.inner_spec,
            'area_id': {
                'name': product_tmpl.area_id.name,
                'id': product_tmpl.area_id.id
            },
            'product_specs': product_tmpl.product_specs,
            'image_medium' : product_tmpl.image_medium,
            'qty_available' : product_tmpl.qty_available,
            'virtual_available' : product_tmpl.virtual_available,
            'categ_id' : product_tmpl.categ_id.name,
        }
        return data