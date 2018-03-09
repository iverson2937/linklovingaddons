# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    manpower_cost = fields.Float(string='工序动作成本', compute='_get_bom_cost')

    def get_bom_cost_new(self):
        result = []
        # for line in self.bom_line_ids:
        #     res.append(self.get_bom_line(line))
        if self.product_tmpl_id.product_ll_type:
            product_type_dict = dict(
                self.product_tmpl_id.fields_get(['product_ll_type'])['product_ll_type']['selection'])
        total_cost = self.product_tmpl_id.product_variant_ids[0].pre_cost_cal_new(raise_exception=False)
        material_cost = self.product_tmpl_id.product_variant_ids[0].get_material_cost_new()
        man_cost = total_cost - material_cost
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
            'material_cost': round(material_cost, 2),
            'manpower_cost': round(man_cost, 2),
            'total_cost': round(total_cost, 2),
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
        total_cost = product_cost * line.product_qty if product_cost else 0
        product_material_cost = line.product_id.get_material_cost_new()
        material_cost = product_material_cost * line.product_qty
        man_cost = total_cost - material_cost

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
            'material_cost': round(material_cost, 2),
            'manpower_cost': round(line.action_id.cost) if line.action_id else '',
            'total_cost': round(total_cost, 2),
            'process_id': process_id,
            'has_extra': False,
            'process_action': line.action_id.name if line.action_id else '',
            "adjust_time": line.adjust_time
        }

        return res

    @api.multi
    def _get_bom_cost(self):
        for bom in self:
            bom.manpower_cost = sum(line.cost for line in bom.bom_line_ids)


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
        total_cost = product_cost * object.product_qty if product_cost else 0
        product_material_cost = object.product_id.get_material_cost_new()
        material_cost = product_material_cost * object.product_qty
        man_cost = total_cost - material_cost

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
            'has_extra': l.bom_id.process_id.has_extra,
            'process_action': l.action_id.name if l.action_id else '',
            'material_cost': round(material_cost, 2),
            'manpower_cost': round(l.action_id.cost, 2) if l.action_id else '',
            'total_cost': round(total_cost, 2),
            'parent_id': parnet.id,
            'qty': l.product_qty,
            'process_id': process_id,
            "adjust_time": l.adjust_time
            # 'bom_ids': bom_line_ids
        }
        result.append(res)

    return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    action_id = fields.Many2one('mrp.process.action')
    cost = fields.Float(string=u'动作成本', related='action_id.cost')
    sub_total_cost = fields.Float(compute='_get_sub_total_cost')
    adjust_time = fields.Float(string=u'调整时间')
    adjust_cost = fields.Float(compute="_get_adjust_total_cost")

    @api.multi
    def _get_adjust_total_cost(self):
        for line in self:
            if line.adjust_time and line.bom_id.process_id.hourly_wage:
                line.adjust_cost = line.bom_id.process_id.hourly_wage * line.adjust_time
            else:
                line.adjust_cost = 0.0

    @api.multi
    def _get_sub_total_cost(self):
        for line in self:
            line.sub_total_cost = (line.cost + line.adjust_cost) * line.product_qty

    @api.one
    def get_action_options(self):
        domain = []
        # if self.bom_id.process_id:
        #     domain = [('process_id', '=', self.bom_id.process_id.id)]
        res = []
        actions = self.env['mrp.process.action'].search(domain)
        for action in actions:
            res.append({
                'id': action.id,
                'name': action.name
            })
        return res

    @api.model
    def save_multi_changes(self, arg, **kwargs):
        bom_id = kwargs.get('bom_id')
        for line in arg:
            bom_line_id = self.env['mrp.bom.line'].browse(line.get('id'))
            bom_line_id.action_id = self.env['mrp.process.action'].browse(line.get('process_action'))
        return self.env['mrp.bom'].browse(int(bom_id)).get_bom_cost_new()
