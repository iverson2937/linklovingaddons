# -*- coding: utf-8 -*-
import json
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def action_deny(self):
        for line in self.bom_line_ids:
            reject_bom_line_product_bom(line)

    @api.multi
    def action_released(self):
        for line in self.bom_line_ids:
            line.set_bom_line_product_bom_released()

    @api.multi
    def bom_detail(self):

        return {
            'type': 'ir.actions.client',
            'tag': 'bom_update',
            'bom_id': self.id
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
            'name': self.product_tmpl_id.name,
            'code': self.product_tmpl_id.default_code,
            'process_id': self.process_id.name,
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
                bom_line_ids.append(_get_rec(l, level))
            if level > 0 and level < 6:
                level -= 1
        bom_id = line.product_id.product_tmpl_id.bom_ids
        process_id = False
        if bom_id:
            process_id = bom_id[0].process_id.name

        res = {
            'name': line.product_id.name,
            'product_id': line.product_id.id,
            'product_tmpl_id': line.product_id.product_tmpl_id.id,
            'is_highlight': line.is_highlight,
            'id': line.id,
            'product_specs': line.product_id.product_specs,
            'code': line.product_id.default_code,
            'uuid': str(uuid.uuid1()),
            'qty': line.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': bom_line_ids
        }

        return res


def _get_rec(object, level, qty=1.0, uom=False):
    for l in object:
        bom_line_ids = []
        if l.child_line_ids:
            if level < 6:
                level += 1
            for line in l.child_line_ids:
                bom_line_ids.append(_get_rec(line, level))
            if level > 0 and level < 6:
                level -= 1
        bom_id = l.product_id.product_tmpl_id.bom_ids
        process_id = False
        if bom_id:
            process_id = bom_id[0].process_id.name
        res = {
            'name': l.product_id.name,
            'product_id': l.product_id.id,
            'product_tmpl_id': l.product_id.product_tmpl_id.id,
            'code': l.product_id.default_code,
            'uuid': str(uuid.uuid1()),
            'product_specs': l.product_id.product_specs,
            'is_highlight': l.is_highlight,
            'id': l.id,
            'qty': l.product_qty,
            'process_id': process_id,
            'level': level,
            'bom_ids': bom_line_ids
        }

    return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    is_highlight = fields.Boolean()

    def set_bom_line_product_bom_released(self):
        self.bom_id.state = 'release'
        # line.bom_id.product_tmpl_id.apply_bom_update()

        if self.child_line_ids:
            for line in self.child_line_ids:
                line.set_bom_line_product_bom_released()

    @api.model
    def create(self, vals):
        line_id = super(MrpBomLine, self).create(vals)
        if line_id.bom_id and line_id.bom_id.state != 'new':
            vals.update({
                'is_highlight': True
            })
            body = (u"添加物料<br/><ul class=o_timeline_tracking_value_list>"
                    + u"<li>产品<span> : </span><span class=o_timeline_tracking_value>%s</span></li>"
                    + u"<li>规格<span> : </span><span class=o_timeline_tracking_value>%s</span></li>"
                    + u"<li>数量<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (
                       line_id.product_id.name, line_id.product_specs, line_id.product_qty)
            line_id.bom_id.message_post(body=body)
            if line_id.bom_id.state == 'release':
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


        return line_id

    @api.multi
    def write(self, vals):

        if (
                'RT-ENG' in self.bom_id.product_tmpl_id.name or self.bom_id.product_tmpl_id.product_ll_type == 'semi-finished') \
                and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'你没有权限修改请联系管理员')

        if self.bom_id.state != 'new' and 'action_line_ids' not in vals:
            vals.update({
                'is_highlight': True
            })
            body = u"BOM被修改.<br/><ul class=o_timeline_tracking_value_list>"
            product_id = False
            if 'product_id' in vals:
                product_id = vals.get('product_id')
                new_product = self.env['product.product'].browse(product_id).name
                body += (u"<li>产品<span> : </span><span class=o_timeline_tracking_value>%s-->%s</span></li>") % (
                    self.product_id.name, new_product)
            elif 'product_qty' in vals:
                product_id = product_id if product_id else self.product_id.name

                body += (u"<li>%s数量<span> : </span><span class=o_timeline_tracking_value>%s-->%s</span></li>") % (
                    product_id,
                    self.product_qty, vals.get('product_qty'))
            elif 'product_specs' in vals:
                product_id = product_id if product_id else self.product_id.name
                body += (u"<li>%s规格<span> : </span><span class=o_timeline_tracking_value>%s-->%s</span></li>") % (
                    product_id,
                    self.product_specs, vals.get('product_specs'))
            else:
                body += '</ul>'

            self.bom_id.message_post(body=body)
        return super(MrpBomLine, self).write(vals)

    @api.multi
    def unlink(self):
        if (
                'RT-ENG' in self.bom_id.product_tmpl_id.name or self.bom_id.product_tmpl_id.product_ll_type == 'semi-finished') \
                and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise UserError(u'你没有权限修改请联系管理员')
        if self.bom_id and self.bom_id.state != 'new':
            for line_id in self:
                body = (u"删除物料<br/><ul class=o_timeline_tracking_value_list>"
                        + u"<li>产品<span> : </span><span class=o_timeline_tracking_value>%s</span></li>"
                        + u"<li>规格<span> : </span><span class=o_timeline_tracking_value>%s</span></li>"
                        + u"<li>数量<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (
                           line_id.product_id.name, line_id.product_specs, line_id.product_qty)
                self.bom_id.message_post(body=body)
        return super(MrpBomLine, self).unlink()

    # @api.model
    # def create(self, vals):
    #     if 'bom_id' in vals:
    #         product_id = self.env['mrp.bom'].browse(vals['bom_id']).product_tmpl_id
    #         if ('RT-ENG' in product_id.name or product_id.product_ll_type == 'semi-finished') \
    #                 and not self.env.user.has_group('mrp.group_mrp_manager'):
    #             raise UserError(u'你没有权限修改请联系管理员')
    #     return super(MrpBomLine, self).create(vals)

    @api.multi
    def toggle_highlight(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        for record in self:
            record.is_highlight = not record.is_highlight


def get_next_default_code(default_code):
    if not default_code:
        raise UserError(u'产品没有对应料号')

    version = default_code.split('.')[-1]

    return int(version) + 1


def reject_bom_line_product_bom(line):
    line.bom_id.state = 'deny'
