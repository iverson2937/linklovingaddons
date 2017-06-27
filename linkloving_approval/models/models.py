# -*- coding: utf-8 -*-

from odoo import models, fields, api

APPROVAL_TYPE = [('waiting_submit', '待提交'),
                 ('submitted', '已提交'),
                 ('waiting_approval', '待审批'),
                 ('approval', '已审批')]


class ApprovalCenter(models.TransientModel):
    _name = 'approval.center'

    type = fields.Selection(string=u"类型", selection=APPROVAL_TYPE, default='waiting_submit', required=False, )

    res_model = fields.Char('Related Model', help='Model of the followed resource')

    def get_attachment_info_by_type(self):
        attatchments = self.env[self.res_model].search([('create_uid', '=', self.env.user.id),
                                                        ('state', '=', 'waiting_release')])

        attach_list = []
        for atta in attatchments:
            attach_list.append(self.env["product.attachment.info"].convert_attachment_info(atta))
        return attach_list

    def fields_get(self, allfields=None, attributes=None):
        return super(ApprovalCenter, self).fields_get(allfields, attributes)
    
# class ProductAttachmentInfo(models.Model):
#     _inherit = 'product.attachment.info'
