# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression

APPROVAL_TYPE = [('waiting_submit', '待提交'),
                 ('submitted', '已提交'),
                 ('waiting_approval', '待我审批'),
                 ('approval', '我已审批')]


class ApprovalCenter(models.TransientModel):
    _name = 'approval.center'

    type = fields.Selection(string=u"类型", selection=APPROVAL_TYPE, default='waiting_submit', required=False, )

    res_model = fields.Char('Related Model', help='Model of the followed resource')

    def get_bom_info_by_type(self, offset, limit):
        if self.type == 'waiting_submit':
            domain = [('current_review_id', '=', self.env.user.id),
                      ('state', 'in',
                       ['waiting_release', 'cancel', 'deny', 'new', 'updated'])]
            bom_ids = self.env[self.res_model].search(domain,
                                                      limit=limit, offset=offset, order='sequence,write_date desc')
        elif self.type == 'submitted':
            domain = [('current_review_id', '=', self.env.user.id)]
            bom_ids = self.env[self.res_model].search(domain,
                                                      limit=limit, offset=offset, order='sequence,write_date desc')
        elif self.type == 'waiting_approval':
            lines = self.env["review.process.line"].search([("state", '=', 'waiting_review'),
                                                            ('partner_id', '=', self.env.user.partner_id.id)],
                                                           )
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids),
                      ('state', 'in', ['review_ing'])]
            bom_ids = self.env[self.res_model].search(domain, limit=limit, offset=offset, order='write_date desc')
        elif self.type == 'approval':
            lines = self.env["review.process.line"].search([("state", 'not in', ['waiting_review', 'review_canceled']),
                                                            ('partner_id', '=', self.env.user.partner_id.id),
                                                            ('review_order_seq', '!=', 1)],
                                                           )
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids)]
            bom_ids = self.env[self.res_model].search(domain,
                                                      limit=limit, offset=offset, order='write_date desc')

        bom_list = []
        for bom in bom_ids:
            bom_list.append(bom.convert_bom_info())
        length = self.env[self.res_model].search_count(domain)

        return {'bom_list': bom_list, 'length': length}

    def get_attachment_info_by_type(self, offset, limit):

        if self.type == 'waiting_submit':
            domain = [('create_uid', '=', self.env.user.id),
                      ('state', 'in', ['waiting_release', 'cancel', 'deny'])]
            attatchments = self.env[self.res_model].search(domain,
                                                           limit=limit, offset=offset, order='create_date desc')
        elif self.type == 'submitted':
            domain = [('create_uid', '=', self.env.user.id),
                      (
                          'state', 'not in',
                          ['waiting_release', 'draft', 'cancel'])]
            attatchments = self.env[self.res_model].search(domain,
                                                           limit=limit, offset=offset, order='create_date desc')
        elif self.type == 'waiting_approval':

            lines = self.env["review.process.line"].search([("state", '=', 'waiting_review'),
                                                            ('partner_id', '=', self.env.user.partner_id.id)],
                                                           order='create_date desc')
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids),
                      ('state', 'in', ['review_ing'])]
            attatchments = self.env[self.res_model].search(domain,
                                                           limit=limit,
                                                           offset=offset, )
        elif self.type == 'approval':

            lines = self.env["review.process.line"].search([("state", 'not in', ['waiting_review', 'review_canceled']),
                                                            ('partner_id', '=', self.env.user.partner_id.id),
                                                            ('review_order_seq', '!=', 1)],
                                                           order='create_date desc')
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids)]
            attatchments = self.env[self.res_model].search(domain,
                                                           order='create_date desc',
                                                           limit=limit,
                                                           offset=offset, )

        attach_list = []
        for atta in attatchments:
            attach_list.append(atta.convert_attachment_info())

        length = self.env[self.res_model].search_count(domain)
        return {"records": attach_list,
                "length": length
                }

    def get_attachment_info_by_types(self, **kwargs):
        # domain_my = []

        limit = kwargs.get("limit")
        offset = kwargs.get("offset")
        domain_my = kwargs.get("domains")
        print domain_my

        # for i in range(len(domains) - 1):
        #     domain_my.append('|')
        # for domins_one in domains:
        #     if type(domins_one) == dict:
        #         for sss in domins_one.get('__domains'):
        #             if len(sss[0]) == 3:
        #                 domain_my.append(tuple(sss[0]))
        #             else:
        #                 domain_my.append(sss[0])
        #     else:
        #         if len(domins_one) == 1:
        #             domain_my.append(tuple(domins_one[0]))
        #         else:
        #             for index in range(len(domains) - 1):
        #                 domain_my.append('|')
        #             for list_one in domains:
        #                 domain_my.append(tuple(list_one[0]))
        if self.type == 'waiting_submit':
            domain = [('create_uid', '=', self.env.user.id),
                      ('state', 'in', ['waiting_release', 'cancel', 'deny'])]
            attatchments = self.env[self.res_model].search(expression.AND([domain, domain_my]),
                                                           limit=limit, offset=offset, order='create_date desc')
        elif self.type == 'submitted':
            domain = [('create_uid', '=', self.env.user.id),
                      (
                          'state', 'not in',
                          ['waiting_release', 'draft', 'cancel'])]
            attatchments = self.env[self.res_model].search(expression.AND([domain, domain_my]),
                                                           limit=limit, offset=offset, order='create_date desc')
        elif self.type == 'waiting_approval':

            lines = self.env["review.process.line"].search([("state", '=', 'waiting_review'),
                                                            ('partner_id', '=', self.env.user.partner_id.id)],
                                                           order='create_date desc')
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids),
                      ('state', 'in', ['review_ing'])]
            attatchments = self.env[self.res_model].search(expression.AND([domain, domain_my]),
                                                           limit=limit,
                                                           offset=offset, )
        elif self.type == 'approval':

            lines = self.env["review.process.line"].search([("state", 'not in', ['waiting_review', 'review_canceled']),
                                                            ('partner_id', '=', self.env.user.partner_id.id),
                                                            ('review_order_seq', '!=', 1)],
                                                           order='create_date desc')
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids)]
            attatchments = self.env[self.res_model].search(expression.AND([domain, domain_my]),
                                                           order='create_date desc',
                                                           limit=limit,
                                                           offset=offset, )

        attach_list = []
        for atta in attatchments:
            attach_list.append(atta.convert_attachment_info())

        length = self.env[self.res_model].search_count(expression.AND([domain, domain_my]))
        return {"records": attach_list,
                "length": length
                }

    def fields_get(self, allfields=None, attributes=None):
        return super(ApprovalCenter, self).fields_get(allfields=allfields, attributes=attributes)
