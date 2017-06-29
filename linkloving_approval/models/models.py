# -*- coding: utf-8 -*-

from odoo import models, fields, api

APPROVAL_TYPE = [('waiting_submit', '待提交'),
                 ('submitted', '已提交'),
                 ('waiting_approval', '待我审批'),
                 ('approval', '我已审批')]


class ApprovalCenter(models.TransientModel):
    _name = 'approval.center'

    type = fields.Selection(string=u"类型", selection=APPROVAL_TYPE, default='waiting_submit', required=False, )

    res_model = fields.Char('Related Model', help='Model of the followed resource')

    def get_attachment_info_by_type(self, offset, limit):
        if self.type == 'waiting_submit':
            attatchments = self.env[self.res_model].search([('create_uid', '=', self.env.user.id),
                                                            ('state', '=', 'waiting_release')],
                                                           limit=limit, offset=offset)
        elif self.type == 'submitted':
            attatchments = self.env[self.res_model].search([('create_uid', '=', self.env.user.id),
                                                            (
                                                            'state', 'not in', ['waiting_release', 'draft', 'cancel'])],
                                                           limit=limit, offset=offset)
        elif self.type == 'waiting_approval':
            lines = self.env["review.process.line"].search([("state", '=', 'waiting_review'),
                                                            ('partner_id', '=', self.env.user.partner_id.id)],
                                                           limit=limit, offset=offset)
            review_ids = lines.mapped("review_id")
            attatchments = self.env[self.res_model].search([("review_id", "in", review_ids.ids)])
        elif self.type == 'approval':
            lines = self.env["review.process.line"].search([("state", 'not in', ['waiting_review', 'review_canceled']),
                                                            ('partner_id', '=', self.env.user.partner_id.id)],
                                                           limit=limit, offset=offset)
            review_ids = lines.mapped("review_id")
            attatchments = self.env[self.res_model].search([("review_id", "in", review_ids.ids)])

        attach_list = []
        for atta in attatchments:
            attach_list.append(atta.convert_attachment_info())
        return attach_list
    
    def fields_get(self, allfields=None, attributes=None):
        return super(ApprovalCenter, self).fields_get(allfields=allfields, attributes=attributes)
    
# class ProductAttachmentInfo(models.Model):
#     _inherit = 'product.attachment.info'
