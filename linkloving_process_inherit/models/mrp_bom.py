# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    cost = fields.Float(string='BOM成本', compute='_get_bom_cost')

    def get_bom(self):
        res = []
        for line in self.bom_line_ids:
            res.append(self.get_bom_line(line))

        result = {
            'bom_id': self.id,
            'product_id': self.product_tmpl_id.id,
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_specs': self.product_tmpl_id.product_specs,
            'name': self.product_tmpl_id.name_get()[0][1],
            'code': self.product_tmpl_id.default_code,
            'process_id': [self.process_id.id, self.process_id.name],
            'bom_ids': sorted(res, key=lambda product: product['code']),
        }

        return result

    def get_bom_line(self, line, level=0):
        bom_line_ids = []
        if line.child_line_ids:
            if level < 6:
                level += 1
            for l in line.child_line_ids:
                bom_line_ids.append(_get_rec(l, level, line))
            if level > 0 and level < 6:
                level -= 1
        bom_id = line.product_id.product_tmpl_id.bom_ids
        action = line.action_id

        process_id = action_id = []
        if bom_id:
            process_id = bom_id[0].process_id.name
        if action:
            action_id = action_id.name

        res = {
            'name': line.product_id.name_get()[0][1],
            'product_type': line.product_id.product_ll_type,
            'product_id': line.product_id.id,
            'product_tmpl_id': line.product_id.product_tmpl_id.id,
            'id': line.id,
            'parent_id': line.bom_id.id,
            'product_specs': line.product_id.product_specs,
            'code': line.product_id.default_code,
            'qty': line.product_qty,
            'process_id': process_id,
            'action_id': action_id,
            'level': level,
            'bom_ids': sorted(bom_line_ids, key=lambda product: product['code'])
        }

        return res

    @api.multi
    def _get_bom_cost(self):
        for bom in self:
            bom.cost = sum(line.cost for line in bom.bom_line_ids)


def _get_rec(object, level, parnet, qty=1.0, uom=False):
    for l in object:
        bom_line_ids = []
        if l.child_line_ids:
            if level < 6:
                level += 1
            for line in l.child_line_ids:
                bom_line_ids.append(_get_rec(line, level, l))
            if level > 0 and level < 6:
                level -= 1
        bom_id = l.product_id.product_tmpl_id.bom_ids
        process_id = []
        if bom_id:
            process_id = [bom_id[0].process_id.id, bom_id[0].process_id.name]

        res = {
            'name': l.product_id.name_get()[0][1],
            'product_id': l.product_id.id,
            'product_tmpl_id': l.product_id.product_tmpl_id.id,
            'code': l.product_id.default_code,
            'product_specs': l.product_id.product_specs,
            # 'is_highlight': l.is_highlight,
            # 'product_type': l.product_id.product_ll_type,
            'id': l.id,
            'material_cost': '',
            'manpower_cost': '',
            'parent_id': parnet.id,
            'qty': l.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': bom_line_ids
        }

    return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    action_id = fields.Many2one('mrp.process.action')
    cost = fields.Float(string=u'动作成本', related='action_id.cost')
    sub_total_cost = fields.Float(compute='_get_sub_total_cost')

    @api.multi
    def _get_sub_total_cost(self):
        for line in self:
            line.sub_total_cost = line.cost * line.product_qty
