# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BatchApprovalWizard(models.TransientModel):
    _name = 'batch.approval.wizard'
    partner_id = fields.Many2one('res.partner')
    remark = fields.Char(string=u'备注')
    cur_partner_id = fields.Many2one('res.partner', default=lambda self: self.env.user.partner_id)

    @api.multi
    def action_to_next(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['mrp.bom'].browse(active_ids):
            # if record.review_id and record.review_id.who_review_now != self.env.user.partner_id:
            #     raise UserError(u'%s不属于你提交' % record.product_tmpl_id.name)
            if record.state == 'release':
                raise UserError(u'%s正式BOM无需送审' % record.product_tmpl_id.name)

            if not record.review_id:  # 如果没审核过
                record.action_send_to_review()

            record.state = 'review_ing'  # 被拒之后 修改状态 wei 审核中
            record.review_id.process_line_review_now.submit_to_next_reviewer(
                review_type='bom_review',
                to_last_review=False,
                partner_id=self.partner_id,
                remark=self.remark, material_requests_id=None, bom_id=record)

    @api.multi
    def action_pass(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['mrp.bom'].browse(active_ids):
            if not record.review_id:
                raise UserError(u'%s没经过送审' % record.product_tmpl_id.name)

            # if record.review_id and record.review_id.who_review_now != self.env.user.partner_id:
            #     raise UserError(u'%s不属于你提交' % record.product_tmpl_id.name)

            record.action_released()
            record.review_id.review_line_ids.filtered(lambda x: x.state == 'waiting_review').action_pass(self.remark,
                                                                                                         None, record)
