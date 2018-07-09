# -*- coding: utf-8 -*-
import json
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    _order = 'sequence,write_date'

    review_id = fields.Many2one("review.process",
                                string=u'待...审核',
                                track_visibility='always',
                                readonly=True, copy=False)
    who_review_now = fields.Many2one("res.partner", related='review_id.who_review_now')
    current_review_id = fields.Many2one('res.users')

    sequence = fields.Integer(compute='_get_sequence', store=True)

    def check_can_update(self):
        updateable_states = ('draft', 'confirmed', 'waiting_material', 'done', 'cancel')
        mo_ids = self.env['mrp.production'].search([('product_tmpl_id', '=', self.product_tmpl_id.id), (
            'state', 'not in', updateable_states)])
        if mo_ids:
            raise UserError('有相关生产单在生产中,不可以修改改产品BOM,请联系生产管理员')

    # bom的排序
    @api.multi
    @api.depends('product_tmpl_id.product_ll_type')
    def _get_sequence(self):
        for bom in self:
            if bom.product_tmpl_id.product_ll_type == 'finished':
                bom.sequence = 1
            else:
                bom.sequence = 2

    @api.model
    def create(self, vals):

        bom = super(MrpBom, self).create(vals)
        bom.current_review_id = bom.create_uid
        return bom

    @api.multi
    def bom_approval_status(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'approval_bom',
            'bom_id': self.id,
        }

    @api.multi
    def write(self, vals):
        # self.check_can_update()

        if 'bom_line_ids' in vals:
            if self.state == 'review_ing':
                raise UserError('此bom正在审核中,请取消审核后再做修改')

            # 2017/08/29 还是取消这样的限制,销售单太多取消太麻烦，取消后会重新生成出库单，很困扰
            # product_ids = self.product_tmpl_id.product_variant_ids
            # 有未出货的bom 不允许修改
            # if product_ids:
            #     lines = self.env['sale.order.line'].search(
            #         [('product_id', '=', product_ids.ids[0]), ('state', 'in', ('sale', 'done'))]).filtered(
            #         lambda x: x.product_uom_qty > x.qty_delivered)
            #     if lines:
            #         for line in lines:
            #             if line.procurement_ids.filtered(lambda x: x.state not in ('cancel', 'done')):
            #                 raise UserError(_(u'销售单 %s 未发完货,不可以修改BOM,请联系销售取消相关销售单') % (line.order_id.name,))
            if self.state == 'review_ing':
                raise UserError('Bom 在审核中,请先让审核人退回，再做修改')

            if self.state not in ('new', 'updated', 'deny', 'cancel'):
                if not self.review_id:
                    self.review_id = self.env["review.process"].create_review_process('mrp.bom',
                                                                                      self.id)
                else:
                    line_ids = self.review_id.get_review_line_list()
                    self.env["review.process.line"].create({
                        'partner_id': self.env.user.partner_id.id,
                        'review_id': self.review_id.id,
                        'remark': '%s----->%s' % (self.state, u'更新'),
                        'state': 'waiting_review',
                        'last_review_line_id': line_ids[-1].get('id') if line_ids else False,
                        'review_order_seq': max([line.review_order_seq for line in self.review_id.review_line_ids]) + 1
                    })

                vals.update({
                    'current_review_id': self.env.user.id,
                    'state': 'updated',
                })
        return super(MrpBom, self).write(vals)

    @api.multi
    def bom_detail_new(self):

        return {
            'type': 'ir.actions.client',
            'tag': 'new_bom_update',
            'bom_id': self.id,
            'is_show': True,
        }

    @api.multi
    def bom_approval(self):

        return {
            'type': 'ir.actions.client',
            'tag': 'bom_approval',
            'bom_id': self.id,
        }

    def get_bom(self):
        res = []
        for line in self.bom_line_ids:
            res.append(self.get_bom_line(line))

        result = {
            'uuid': str(uuid.uuid1()),
            'bom_id': self.id,
            'product_id': self.product_tmpl_id.id,
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_specs': self.product_tmpl_id.product_specs,
            'name': self.product_tmpl_id.name_get()[0][1],
            'code': self.product_tmpl_id.default_code,
            'process_id': [self.process_id.id, self.process_id.name],
            'bom_ids': sorted(res, key=lambda product: product['code']),
            'state': self.state,
            'review_line': self.review_id.get_review_line_list(),
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
        process_id = []
        if bom_id:
            process_id = [bom_id[0].process_id.id, bom_id[0].process_id.name]

        res = {
            'name': line.product_id.name_get()[0][1],
            'product_type': line.product_id.product_ll_type,
            'product_id': line.product_id.id,
            'product_tmpl_id': line.product_id.product_tmpl_id.id,
            'is_highlight': line.is_highlight,
            'id': line.id,
            'parent_id': line.bom_id.id,
            'product_specs': line.product_id.product_specs,
            'code': line.product_id.default_code,
            'uuid': str(uuid.uuid1()),
            'qty': line.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': sorted(bom_line_ids, key=lambda product: product['code'])
        }

        return res


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
            'is_highlight': l.is_highlight,
            'product_type': l.product_id.product_ll_type,
            'id': l.id,
            'parent_id': parnet.id,
            'qty': l.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': bom_line_ids
        }

    return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.model
    def create(self, vals):
        print vals, 'create'
        return super(MrpBomLine, self).create(vals)

    @api.multi
    def write(self, vals):
        print vals, 'write'
        return super(MrpBomLine, self).write(vals)

    @api.multi
    def unlink(self):
        print self, 'unlink'
        return super(MrpBomLine, self).unlink()


class MrpBomTemporary(models.Model):
    _name = "mrp.bom.temporary"

    bom_type = fields.Selection([('bom_structure', u'Bom 结构'), ('bom_costing', u'Bom 成本')], string=u'导出类型',
                                default='bom_structure')

    @api.multi
    def get_product_bom(self):

        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        file_type = 'bom_structure' if self.bom_type == 'bom_structure' else 'bom_costing'

        print self.id
        return {
            'type': 'ir.actions.act_url',
            'url': '/linkloving_new_bom_update/linkloving_new_bom_update?model=mrp.bom&id_list=%s&file_type=%s' % (
                active_ids, file_type),
            'target': 'new',
        }
