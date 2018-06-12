# -*- coding: utf-8 -*-

from odoo import models, fields, api

BOM_STATE = {
    'draft': u'草稿',
    'waiting_release': u'等待提交审核',
    'review_ing': u'审核中',
    'release': u'已发布',
    'deny': u'被拒',
    'cancel': u"已取消",
    'new': u'新建',
    'updated': u'更改'
}


class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    is_show_action_deny = fields.Boolean(string=u'是否显示审核不通过', default=True, compute='_compute_is_show_action_deny')
    need_sop = fields.Selection([
        (1, u'需要'),
        (2, u'不需要'),
    ], string=u'是否需要SOP文件')

    has_right_to_review = fields.Boolean(compute='_compute_has_right_to_review')

    @api.multi
    def _compute_is_show_cancel(self):
        for info in self:
            if self.env.user.id == info.current_review_id.id and info.state in ('review_ing', 'deny', 'cancel'):
                info.is_show_cancel = True

    is_show_cancel = fields.Boolean(compute='_compute_is_show_cancel')

    @api.multi
    def _compute_is_show_action_deny(self):
        for info in self:
            if info.create_uid.id == self.env.user.id and info.state in ['waiting_release', 'new', 'cancel', 'deny']:
                info.is_show_action_deny = False
            else:
                info.is_show_action_deny = True

    @api.multi
    def _compute_has_right_to_review(self):
        for info in self:
            if self.env.user.id in info.review_id.who_review_now.user_ids.ids and info.state in ['review_ing']:
                info.has_right_to_review = True

    def convert_bom_info(self):
        return {
            'product_id': {
                'id': self.product_tmpl_id.id,
                'name': self.product_tmpl_id.display_name,
                'product_specs': self.product_tmpl_id.product_specs,

            },
            'id': self.id,
            'uom_name': self.product_uom_id.name,
            'process_name': self.process_id.name,
            'product_qty': self.product_qty,
            'review_id': self.sudo().review_id.who_review_now.name or '',
            'state': [self.state, BOM_STATE[self.state]],
            'has_right_to_review': self.has_right_to_review,
            'review_line': self.review_id.get_review_line_list(),
            # 'is_able_to_use': self.is_able_to_use,
            'is_show_cancel': self.is_show_cancel,
            # 'is_first_review': self.is_first_review,
            'is_show_action_deny': self.is_show_action_deny,
            'create_uid_name': self.sudo().create_uid.name,
            'create_date': self.create_date,
            'write_date': self.write_date
        }

    review_id = fields.Many2one("review.process",
                                string=u'待...审核',
                                track_visibility='onchange',
                                readonly=True, copy=False)

    @api.multi
    def action_send_to_review(self):
        if not self.review_id:
            self.review_id = self.env["review.process"].create_review_process('mrp.bom', self.id)
