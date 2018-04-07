# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    manpower_cost = fields.Float(string='工序动作成本', compute='_get_bom_cost')

    @api.model
    def get_diff_bom_data(self, **kwargs):
        bom_obj = self.env['mrp.bom']
        source_id = kwargs.get("origin_bom_id")
        dest_id = kwargs.get("target_bom_id")
        source_bom = bom_obj.browse(source_id)
        dest_bom = bom_obj.browse(dest_id)
        source_bom_product_ids = source_bom.mapped('bom_line_ids.product_id').ids
        dest_bom_product_ids = dest_bom.mapped('bom_line_ids.product_id').ids
        common_products = set(source_bom_product_ids) & set(dest_bom_product_ids)
        datas = []
        for product in common_products:
            source_line = source_bom.bom_line_ids.filtered(lambda x: x.product_id.id == product)
            dest_line = dest_bom.bom_line_ids.filtered(lambda x: x.product_id.id == product)
            datas.append({
                'source_default_code': source_line.product_id.default_code,
                'source_product_name': source_line.product_id.name,
                'source_qty': source_line.product_qty,
                'source_action_ids': source_line.parse_action_line_data(no_option=True, no_data=True),
                'dest_default_code': dest_line.product_id.default_code,
                'dest_product_name': dest_line.product_id.name,
                'dest_qty': dest_line.product_qty,
                'dest_action_ids': dest_line.parse_action_line_data(no_option=True, no_data=True),
                'dest_bom_line': dest_line.id,
                'no_edit': True
            })

        for s_product in source_bom_product_ids:
            source_line = source_bom.bom_line_ids.filtered(lambda x: x.product_id.id == s_product)
            if s_product not in common_products:
                datas.append({
                    'source_default_code': source_line.product_id.default_code,
                    'source_product_name': source_line.product_id.name,
                    'source_qty': source_line.product_qty,
                    'source_action_ids': source_line.parse_action_line_data(no_option=True, no_data=True),
                    'dest_default_code': '',
                    'dest_product_name': '',
                    'dest_qty': '',
                    'dest_action_ids': '',
                    'dest_bom_line': '',
                    'no_edit': True
                })
        for d_product in dest_bom_product_ids:
            dest_line = dest_bom.bom_line_ids.filtered(lambda x: x.product_id.id == d_product)
            if d_product not in common_products:
                datas.append({
                    'source_default_code': '',
                    'source_product_name': '',
                    'source_qty': '',
                    'source_action_ids': '',
                    'dest_default_code': dest_line.product_id.default_code,
                    'dest_product_name': dest_line.product_id.name,
                    'dest_qty': dest_line.product_qty,
                    'dest_action_ids': dest_line.parse_action_line_data(no_option=True, no_data=True),
                    'dest_bom_line': dest_line.id,
                    'no_edit': False
                })
        print datas, 'datas'
        return datas

    def get_product_options(self, source_bom_id, dest_bom_id):
        datas = []
        bom_obj = self.env['mrp.bom']
        source_id = source_bom_id
        dest_bom_id = dest_bom_id
        source_bom = bom_obj.browse(source_id)
        dest_bom = bom_obj.browse(dest_bom_id)
        source_bom_product_ids = source_bom.mapped('bom_line_ids.product_id').ids
        dest_bom_product_ids = dest_bom.mapped('bom_line_ids.product_id').ids
        common_products = set(source_bom_product_ids) & set(dest_bom_product_ids)
        for product in source_bom_product_ids:
            ation_data = source_bom.mapped('bom_line_ids').filtered(
                lambda x: x.product_id.id == product)
            if product not in common_products:
                datas.append({
                    'id': product,
                    'action_ids': ation_data.parse_action_line_data(no_option=True, no_data=True),
                    'name': self.env['product.product'].browse(product).name
                })
        return datas

    @api.model
    def save_changes(self, args, **kwargs):
        source_bom_id = kwargs.get('source_bom_id')
        # for arg in args:
        #     product_id = arg.get('product_id')
        #     ation_datas = self.env['mrp.bom'].brose(source_bom_id).mapped('bom_line_ids').filtered(
        #         lambda x: x.product_id.id == product_id)
        #     bom_line_id = arg.get('bom_line_id')
        #     for action in ation_datas:
        #         self.env['mrp.action.line'].create({
        #             'action_id': action.action_id,
        #             'rate': action.rate,
        #             'rate_2': action.rate_2,
        #             'bom_line_id': bom_line_id
        #         })

        return 'ok'

    # 搜索bom
    @api.model
    def get_bom_list(self, arg):
        product_name = arg.get('name')
        product_tmpl_ids = self.env['product.template'].search(
            [('bom_ids', '!=', False), '|', ('name', 'ilike', product_name), ('default_code', 'ilike', product_name)],
            limit=10)
        bom_list = []
        for product_tmpl_id in product_tmpl_ids:
            if product_tmpl_id.bom_count > 1:
                raise UserError('%s有超过一个Bom,请核对') % product_tmpl_id.name
            else:
                bom_list.append({
                    'id': product_tmpl_id.bom_ids[0].id,
                    'name': product_tmpl_id.display_name
                })
        return bom_list

    def get_bom_line_list(self):
        line_list = []
        for line in self.bom_line_ids:
            line_list.append({
                'source_default_code': line.product_id.default_code,
                'source_product_name': line.product_id.name,
                'source_qty': line.product_qty,
                'source_action_ids': line.parse_action_line_data(no_option=True, no_data=True)
            })
        return line_list

    def _get_product_type_dict(self):
        return dict(
            self.product_tmpl_id.fields_get(['product_ll_type'])['product_ll_type']['selection'])

    def get_default_bom_cost(self):
        result = []

        if self.product_tmpl_id.product_ll_type:
            product_type_dict = self._get_product_type_dict()
        total_cost = self.product_tmpl_id.product_variant_ids[0].pre_cost_cal_new(raise_exception=False)

        man_cost = self.product_tmpl_id.product_variant_ids[0].get_pure_manpower_cost()
        material_cost = total_cost - man_cost
        res = {
            'id': 1,
            'pid': 0,
            'bom_id': self.id,
            'product_id': self.product_tmpl_id.id,
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_specs': self.product_tmpl_id.product_specs,
            'name': self.product_tmpl_id.name_get()[0][1],
            'code': self.product_tmpl_id.default_code,
            'process_id': [self.process_id.id, self.process_id.name],
            'product_type': product_type_dict[self.product_tmpl_id.product_ll_type],
            # 'bom_ids': sorted(res, key=lambda product: product['code']),
        }
        result.append(res)
        if self.bom_line_ids:
            line_ids = []
            for line in self.bom_line_ids:
                line_ids.append(self.get_bom_line_default(self.product_tmpl_id.categ_id.id, self.id, line, result,
                                                          product_type_dict))
        return result + sorted(line_ids, key=lambda product: product['code'], reverse=True)

    def get_bom_line_default(self, categ_id, root_bom_id, line, result, product_type_dict):
        '''
        根据系列获取默认值
        :param categ_id:
        :param root_bom_id:
        :param line:
        :param result:
        :param product_type_dict:
        :return:
        '''
        if line.child_line_ids:

            for l in line.child_line_ids:
                _get_rec_default(categ_id, l, line, result, product_type_dict)

        bom_id = line.product_id.product_tmpl_id.bom_ids

        process_id = []
        if bom_id:
            process_id = bom_id[0].process_id.name
        product_cost = line.product_id.pre_cost_cal_new(raise_exception=False)
        line_cost = product_cost if product_cost else 0
        # material_cost = line_cost * line.product_qty
        # man_cost = line.action_id.cost * line.product_qty if line.action_id else 0
        # total_cost = material_cost + man_cost

        # 没有值有默认工序动作默认工序动作
        if not line.parse_action_line_data(no_option=True, no_data=True) and line.get_product_action_default():
            is_default = True
            action_process = line.get_product_action_default()
        else:
            action_process = line.parse_action_line_data(no_option=True)

            is_default = False

        res = {
            'name': line.product_id.name_get()[0][1],
            'product_type': product_type_dict[line.product_id.product_ll_type],
            'product_id': line.product_id.id,
            'product_tmpl_id': line.product_id.product_tmpl_id.id,
            'id': line.id,
            'has_lines': 0 if line.child_line_ids else 1,
            'pid': 1,
            'product_specs': line.product_id.product_specs,
            'code': line.product_id.default_code,
            'qty': line.product_qty,
            # 'material_cost': round(material_cost, 2),
            # 'manpower_cost': round(man_cost, 2),
            # 'total_cost': round(total_cost, 2),
            'process_id': process_id,
            'process_action': action_process,
            'is_default': is_default

        }
        return res

    def get_bom_cost_new(self):
        result = []

        if self.product_tmpl_id.product_ll_type:
            product_type_dict = self._get_product_type_dict()
        total_cost = self.product_tmpl_id.product_variant_ids[0].pre_cost_cal_new(raise_exception=False)

        man_cost = self.product_tmpl_id.product_variant_ids[0].get_pure_manpower_cost()
        material_cost = total_cost - man_cost
        res = {
            'id': 1,
            'pid': 0,
            'bom_id': self.id,
            'product_id': self.product_tmpl_id.id,
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_specs': self.product_tmpl_id.product_specs,
            'name': self.product_tmpl_id.name_get()[0][1],
            'code': self.product_tmpl_id.default_code,
            'process_id': [self.process_id.id, self.process_id.name],
            'product_type': product_type_dict[self.product_tmpl_id.product_ll_type],
            'material_cost': round(material_cost, 5),
            'manpower_cost': round(man_cost, 5),
            'total_cost': round(total_cost, 5),
            # 'bom_ids': sorted(res, key=lambda product: product['code']),
        }
        result.append(res)
        if self.bom_line_ids:
            line_ids = []
            for line in self.bom_line_ids:
                line_ids.append(self.get_bom_line_new(line, result, product_type_dict))
        return result + sorted(line_ids, key=lambda product: product['code'], reverse=True)

    def get_bom_line_new(self, line, result, product_type_dict):
        if line.child_line_ids:

            for l in line.child_line_ids:
                _get_rec(l, line, result, product_type_dict)

        bom_id = line.product_id.product_tmpl_id.bom_ids

        process_id = []
        if bom_id:
            process_id = bom_id[0].process_id.name
        product_cost = line.product_id.pre_cost_cal_new(raise_exception=False)
        line_cost = product_cost if product_cost else 0
        material_cost = line_cost * line.product_qty
        man_cost = line.bom_line_man_cost
        total_cost = material_cost + man_cost

        res = {
            'name': line.product_id.name_get()[0][1],
            'product_type': product_type_dict[line.product_id.product_ll_type],
            'product_id': line.product_id.id,
            'product_tmpl_id': line.product_id.product_tmpl_id.id,
            'id': line.id,
            'has_lines': 0 if line.child_line_ids else 1,
            'pid': 1,
            'product_specs': line.product_id.product_specs,
            'code': line.product_id.default_code,
            'qty': line.product_qty,
            'material_cost': round(material_cost, 5),
            'manpower_cost': round(man_cost, 5),
            'total_cost': round(total_cost, 5),
            'process_id': process_id,
            'process_action': line.parse_action_line_data()

        }

        return res

    @api.multi
    def _get_bom_cost(self):
        for bom in self:
            bom.manpower_cost = sum(bom_line.bom_line_man_cost for bom_line in bom.bom_line_ids)


def _get_rec_default(categ_id, object, parnet, result, product_type_dict):
    for l in object:
        if l.child_line_ids:
            for line in l.child_line_ids:
                _get_rec_default(categ_id, line, l, result, product_type_dict)

        bom_id = l.product_id.product_tmpl_id.bom_ids
        process_id = []
        if bom_id:
            process_id = [bom_id[0].process_id.id, bom_id[0].process_id.name]

        product_cost = object.product_id.pre_cost_cal_new(raise_exception=False)
        line_cost = product_cost if product_cost else 0
        material_cost = line_cost * object.product_qty
        # man_cost = l.action_id.cost if l.action_id else 0
        # total_cost = material_cost + man_cost

        if not l.parse_action_line_data(no_option=True, no_data=True) and l.get_product_action_default():
            is_default = True
            action_process = l.get_product_action_default()
        else:
            action_process = l.parse_action_line_data(no_option=True)
            is_default = False

        res = {
            'name': l.product_id.name_get()[0][1],
            'product_id': l.product_id.id,
            'product_type': product_type_dict[l.product_id.product_ll_type],
            'product_tmpl_id': l.product_id.product_tmpl_id.id,
            'code': l.product_id.default_code,
            'product_specs': l.product_id.product_specs,
            # 'is_highlight': l.is_highlight,
            # 'product_type': l.product_id.product_ll_type,
            'id': l.id,
            'pid': parnet.id,
            'process_action': action_process,
            'is_default': is_default,
            'material_cost': round(material_cost, 2),
            # 'manpower_cost': round(man_cost, 2),
            # 'total_cost': round(total_cost, 2),
            'parent_id': parnet.id,
            'qty': l.product_qty,
            'process_id': process_id,
        }
        result.append(res)

    return res


def _get_rec(object, parnet, result, product_type_dict):
    for l in object:
        if l.child_line_ids:
            for line in l.child_line_ids:
                _get_rec(line, l, result, product_type_dict)

        bom_id = l.product_id.product_tmpl_id.bom_ids
        process_id = []
        if bom_id:
            process_id = [bom_id[0].process_id.id, bom_id[0].process_id.name]

        product_cost = object.product_id.pre_cost_cal_new(raise_exception=False)
        line_cost = product_cost if product_cost else 0
        material_cost = line_cost * object.product_qty
        man_cost = l.bom_line_man_cost
        total_cost = material_cost + man_cost

        res = {
            'name': l.product_id.name_get()[0][1],
            'product_id': l.product_id.id,
            'product_type': product_type_dict[l.product_id.product_ll_type],
            'product_tmpl_id': l.product_id.product_tmpl_id.id,
            'code': l.product_id.default_code,
            'product_specs': l.product_id.product_specs,
            # 'is_highlight': l.is_highlight,
            # 'product_type': l.product_id.product_ll_type,
            'id': l.id,
            'pid': parnet.id,
            'material_cost': round(material_cost, 5),
            'process_action': l.parse_action_line_data(),
            'manpower_cost': round(man_cost, 5),
            'total_cost': round(total_cost, 5),
            'parent_id': parnet.id,
            'qty': l.product_qty,
            'process_id': process_id,
        }
        result.append(res)

    return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    # sub_total_cost = fields.Float(compute='_get_sub_total_cost')
    action_line_ids = fields.One2many('process.action.line', 'bom_line_id')
    action_id = fields.Many2one('mrp.process.action')
    bom_line_man_cost = fields.Float(compute='get_bom_line_man_cost')

    def get_bom_line_man_cost(self):
        for line in self:
            total = 0
            for action_line in line.action_line_ids:
                if action_line.rate_2:
                    amount = action_line.rate_2 * action_line.rate * action_line.action_id.cost
                else:
                    amount = action_line.rate * action_line.action_id.cost * line.product_qty
                total += amount
            line.bom_line_man_cost = total

    def get_product_action_default(self):
        domain = [('category_id', '=', self.bom_id.product_tmpl_id.categ_id.id),
                  ('product_id', '=', self.product_id.id)]
        temp_id = self.env['bom.cost.category.temp'].search(domain)
        res = []
        if temp_id:
            res = json.loads(temp_id.action_data)
        return res

    @api.model
    def get_process_action_options(self, process_id):
        options = []
        domain = []
        if process_id:
            domain = ['|', ('process_id', '=', process_id), ('process_id', '=', False)]
        actions = self.env['mrp.process.action'].search(domain)
        for action in actions:
            options.append({
                'id': action.id,
                'name': action.name,
                'cost': action.cost,
                'remark': action.remark,
            })
        return options

    def parse_action_line_data(self, no_option=False, no_data=False):
        res = []

        process_options = []
        process = self.env['mrp.process'].search([])
        for p in process:
            p_data = {
                'id': p.id,
                'name': p.name,
            }
            process_options.append(p_data)

        if not no_option:
            domain = []
            options = []
            if self.bom_id.process_id:
                domain = ['|', ('process_id', '=', self.bom_id.process_id.id), ('process_id', '=', False)]
            actions = self.env['mrp.process.action'].search(domain)
            for action in actions:
                options.append({
                    'id': action.id,
                    'name': action.name,
                    'cost': action.cost,
                    'remark': action.remark,
                })

        for line in self.action_line_ids:
            domain = ['|', ('process_id', '=', line.action_id.process_id.id), ('process_id', '=', False)]
            actions = self.env['mrp.process.action'].search(domain)
            options = []
            for action in actions:
                options.append({
                    'id': action.id,
                    'name': action.name,
                    'cost': action.cost,
                    'remark': action.remark,
                })
            data = {
                'line_id': line.id,
                'action_id': line.action_id.id,
                'action_name': line.action_id.name,
                'cost': line.action_id.cost,
                'remark': line.action_id.remark,
                'rate': line.rate,
                'rate_2': line.rate_2,
                'options': options,
                'process_id': line.action_id.process_id.id,
                'process_options': process_options
            }
            res.append(data)

        if not res and not no_data:
            options = []
            domain = []
            if self.bom_id.process_id:
                domain = ['|', ('process_id', '=', self.bom_id.process_id.id), ('process_id', '=', False)]
            actions = self.env['mrp.process.action'].search(domain)
            for action in actions:
                options.append({
                    'id': action.id,
                    'name': action.name,
                    'cost': action.cost,
                    'remark': action.remark,
                })
            res.append({
                'line_id': '',
                'rate': 1,
                'rate_2': 0,
                'cost': options[0].get('cost') if options else 0.0,
                'remark': options[0].get('remark', '') if options else '',
                'options': options,
                'process_options': process_options,
                'process_id': self.bom_id.process_id.id,
            })

        return res

    def add_action_line_data(self):
        res = []
        options = []
        process_options = []
        process = self.env['mrp.process'].search([])
        for p in process:
            p_data = {
                'id': p.id,
                'name': p.name,
            }
            process_options.append(p_data)

        domain = []
        if self.bom_id.process_id:
            domain = ['|', ('process_id', '=', self.bom_id.process_id.id), ('process_id', '=', False)]
        actions = self.env['mrp.process.action'].search(domain)
        for action in actions:
            options.append({
                'id': action.id,
                'name': action.name,
                'cost': action.cost,
                'remark': action.remark,
                'process_id': action.process_id.id,
            })

        res.append({
            'line_id': '',
            'rate': 1,
            'rate_2': 0,
            'options': options,
            'process_id': self.bom_id.process_id.id,
            'process_options': process_options,

        })

        return res

    @api.one
    def get_action_options(self):
        domain = []
        if self.bom_id.process_id:
            domain = [('process_id', '=', self.bom_id.process_id.id)]
        res = []
        actions = self.env['mrp.process.action'].search(domain)
        for action in actions:
            res.append({
                'id': action.id,
                'name': action.name
            })
        return res

    @api.model
    def save_multi_changes(self, args, **kwargs):
        bom_id = kwargs.get('bom_id')
        action_line_obj = self.env['process.action.line']
        if type(args) == list:
            abc = {}
            for arg in args:
                abc.update({
                    arg.keys()[0]: arg.values()[0]
                })
            args = abc
        for bom_line_id, actions in args.iteritems():

            if actions:
                bom_line = self.env['mrp.bom.line'].browse(int(bom_line_id))
                for action in actions:
                    if type(action) == dict and action.get('id'):
                        process_action_line = action_line_obj.browse(action.get('id'))
                        action_id_new = int(action.get('action_id'))
                        if action_id_new in self.env['mrp.process.action'].search([]).ids:
                            process_action_line.write({
                                'rate': action.get('rate'),
                                'rate_2': action.get('rate_2'),
                                'action_id': action_id_new
                            })
                    elif action.get('delete_line_id'):
                        action_line_obj.browse(int(action.get('delete_line_id'))).unlink()
                    else:
                        action_line_obj.create({
                            'rate': action.get('rate'),
                            'rate_2': action.get('rate_2'),
                            'action_id': int(action.get('action_id')),
                            'bom_line_id': int(bom_line_id)
                        })
                # else:
                #     self.env['process.action.line'].browse()

                action_data = bom_line.parse_action_line_data(no_option=True, no_data=True)
                category_id = bom_line.bom_id.product_tmpl_id.categ_id.id
                tmp_obj = self.env['bom.cost.category.temp']
                product_id = bom_line.product_id.id
                temp_id = tmp_obj.search(
                    [('category_id', '=', category_id), ('product_id', '=', product_id)], limit=1)
                if temp_id:

                    temp_id.action_data = json.dumps(action_data)
                else:
                    tmp_obj.create({'category_id': bom_line.bom_id.product_tmpl_id.categ_id.id,
                                    'product_id': product_id,
                                    'action_data': json.dumps(action_data)
                                    })

        return self.env['mrp.bom'].browse(int(bom_id)).get_bom_cost_new()
