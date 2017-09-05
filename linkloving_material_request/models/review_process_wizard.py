# -*- coding: utf-8 -*-


from odoo import models, fields, api


class MaterialReviewProcessWizard(models.TransientModel):
    _inherit = 'review.process.wizard'
    material_requests_id = fields.Many2one('material.request')
    material_line = fields.Many2one("review.process.line",
                                    related="material_requests_id.review_id.process_line_review_now")

#
#     # 终审 审核通过
#     def action_pass(self):
#         pass
#
#         return super(MaterialReviewProcessWizard, self).action_pass()
