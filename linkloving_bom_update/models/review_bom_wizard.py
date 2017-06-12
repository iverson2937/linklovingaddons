# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReviewProcessWizard(models.TransientModel):
    _name = 'review.bom.wizard'
    cur_partner_id = fields.Many2one('res.partner', default=lambda self: self.env.user.partner_id)
    bom_id = fields.Many2one("mrp.bom")
    partner_id = fields.Many2one('res.partner', domain=[('employee', '=', True)])
    remark = fields.Text()

    # 送审
    def send_to_review(self):
        to_last_review = self._context.get("to_last_review")  # 是否送往终审
        if not self.bom_id.review_id:  # 如果没审核过
            self.bom_id.action_send_to_review()

        self.bom_id.state = 'review_ing'  # 被拒之后 修改状态 wei 审核中
        self.bom_id.review_id.process_line_review_now.submit_to_next_reviewer(
            partner_id=self.partner_id,
            remark=self.remark)

        return True
