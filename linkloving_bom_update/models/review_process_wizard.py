# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReviewProcessWizard(models.TransientModel):
    _inherit = 'review.process.wizard'

    bom_id = fields.Many2one("mrp.bom")

    # 送审
    def send_to_review(self):
        to_last_review = self._context.get("to_last_review")  # 是否送往终审
        if not self.product_attachment_info_id.review_id:  # 如果没审核过
            self.product_attachment_info_id.action_send_to_review()

        self.product_attachment_info_id.state = 'review_ing'  # 被拒之后 修改状态 wei 审核中
        self.product_attachment_info_id.review_id.process_line_review_now.submit_to_next_reviewer(
            to_last_review=to_last_review,
            partner_id=self.partner_id,
            remark=self.remark)

        return True
