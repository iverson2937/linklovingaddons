# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ReviewBOMWizard(models.TransientModel):
    _name = 'review.bom.wizard'
    cur_partner_id = fields.Many2one('res.partner', default=lambda self: self.env.user.partner_id)
    bom_id = fields.Many2one("mrp.bom")
    partner_id = fields.Many2one('res.partner', domain=[('employee', '=', True)])
    review_order_seq = fields.Integer()
    remark = fields.Text()
    review_process_line = fields.Many2one("review.process.line",
                                          related="bom_id.review_id.process_line_review_now")

    # 送审
    def send_to_review(self):
        to_last_review = self._context.get("to_last_review")  # 是否送往终审
        review_type = self._context.get("review_type")
        if not self.bom_id.review_id:  # 如果没审核过
            self.bom_id.action_send_to_review()

        self.bom_id.state = 'review_ing'  # 被拒之后 修改状态 wei 审核中
        self.bom_id.review_id.process_line_review_now.submit_to_next_reviewer(
            review_type=review_type,
            to_last_review=to_last_review,
            partner_id=self.partner_id,
            remark=self.remark)

        return True

    # 终审 审核通过
    def action_pass(self):
        # 审核通过
        self.review_process_line.action_approve(self.remark)
        # 改变文件状态
        self.bom_id.action_released()

        return True

    # 审核不通过
    def action_deny(self):
        self.review_process_line.action_deny(self.remark)
        # 改变文件状态
        self.bom_id.action_deny()

        return True
