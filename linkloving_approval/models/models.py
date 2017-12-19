# -*- coding: utf-8 -*-


ATTACHINFO_FIELD = ['product_tmpl_id', 'file_name', 'review_id', 'remote_path',
                    'version', 'state', 'has_right_to_review', 'is_show_outage',
                    'is_able_to_use', 'is_show_cancel', 'is_first_review',
                    'create_uid', 'type', 'is_delect_view', 'is_show_action_deny', 'create_date']

from odoo import models, fields, api
from odoo.osv import expression


class PdmConfigSetting(models.TransientModel):
    _name = 'pdm.config.settings'
    _inherit = 'res.config.settings'

    pdm_intranet_ip = fields.Char(string=u'内网地址', default='192.168.2.6')
    pdm_external_ip = fields.Char(string=u'外网地址', default='221.224.85.74')
    pdm_port = fields.Char(string=u'端口', default='21')
    op_path = fields.Char(string=u'操作路径', default='/home/pdm/')
    pdm_account = fields.Char(string=u'账号', default='pdm')
    pdm_pwd = fields.Char(string=u'密码', default='robotime')

    @api.model
    def get_default_pdm_intranet_ip(self, m_fields):
        dica = {}
        for fi in m_fields:
            fi_val = self.env["ir.config_parameter"].get_param("pdm.config.settings.%s" % fi, default=None)
            dica.update({
                fi: fi_val
            })

        return dica

    @api.multi
    def set_pdm_intranet_ip(self):
        m_fields = ['pdm_intranet_ip', 'pdm_external_ip', 'pdm_port', 'op_path', 'pdm_account', 'pdm_pwd']
        for record in self:
            for fi in m_fields:
                self.env['ir.config_parameter'].set_param("pdm.config.settings.%s" % fi, getattr(record, fi, ''))


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

    def get_attachment_info_by_type(self, offset, limit, **kwargs):
        domain_my = kwargs.get("domains") or []

        if self.type == 'waiting_submit':
            domain = [('create_uid', '=', self.env.user.id),
                      ('state', 'in', ['waiting_release', 'cancel', 'deny'])]
            attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                limit=limit,
                                                                offset=offset,
                                                                order='create_date desc',
                                                                fields=ATTACHINFO_FIELD)
        elif self.type == 'submitted':
            domain = [('create_uid', '=', self.env.user.id),
                      (
                          'state', 'not in',
                          ['waiting_release', 'draft', 'cancel', 'deny'])]
            attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                limit=limit,
                                                                offset=offset,
                                                                order='create_date desc',
                                                                fields=ATTACHINFO_FIELD)
        elif self.type == 'waiting_approval':

            lines = self.env["review.process.line"].search([("state", '=', 'waiting_review'),
                                                            ('partner_id', '=', self.env.user.partner_id.id)],
                                                           order='create_date desc')
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids),
                      ('state', 'in', ['review_ing'])]
            attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                limit=limit,
                                                                offset=offset,
                                                                fields=ATTACHINFO_FIELD)
        elif self.type == 'approval':

            lines = self.env["review.process.line"].search([("state", 'not in', ['waiting_review', 'review_canceled']),
                                                            ('partner_id', '=', self.env.user.partner_id.id),
                                                            ('review_order_seq', '!=', 1)],
                                                           order='create_date desc')
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids)]
            attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                order='create_date desc',
                                                                limit=limit,
                                                                offset=offset,
                                                                fields=ATTACHINFO_FIELD)

        attach_list = []
        for atta in attatchments:
            # attach_list.append(atta.convert_attachment_info())
            attach_list.append(
                dict(self.env['product.attachment.info'].convert_attachment_info(atta),
                     **{'checkbox_type': self.type, 'create_date': atta.get('create_date')}))

        length = self.env[self.res_model].search_count(expression.AND([domain, domain_my]))
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
            attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                limit=limit, offset=offset, order='create_date desc',
                                                                fields=ATTACHINFO_FIELD)
        elif self.type == 'submitted':
            domain = [('create_uid', '=', self.env.user.id),
                      (
                          'state', 'not in',
                          ['waiting_release', 'draft', 'cancel'])]
            attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                limit=limit, offset=offset, order='create_date desc',
                                                                fields=ATTACHINFO_FIELD)
        elif self.type == 'waiting_approval':

            lines = self.env["review.process.line"].search([("state", '=', 'waiting_review'),
                                                            ('partner_id', '=', self.env.user.partner_id.id)],
                                                           order='create_date desc')
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids),
                      ('state', 'in', ['review_ing'])]
            attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                limit=limit,
                                                                offset=offset,
                                                                fields=ATTACHINFO_FIELD)
        elif self.type == 'approval':

            lines = self.env["review.process.line"].search([("state", 'not in', ['waiting_review', 'review_canceled']),
                                                            ('partner_id', '=', self.env.user.partner_id.id),
                                                            ('review_order_seq', '!=', 1)],
                                                           order='create_date desc')
            review_ids = lines.mapped("review_id")
            domain = [("review_id", "in", review_ids.ids)]
            attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                order='create_date desc',
                                                                limit=limit,
                                                                offset=offset,
                                                                fields=ATTACHINFO_FIELD)

        attach_list = []
        for atta in attatchments:
            res = self.env['product.attachment.info'].convert_attachment_info(atta)
            res.update({
                'checkbox_type': self.type
            })
            attach_list.append(res)
            # attach_list.append(dict(atta.convert_attachment_info(), **{'checkbox_type': self.type}))

        length = self.env[self.res_model].search_count(expression.AND([domain, domain_my]))
        return {"records": attach_list,
                "length": length
                }

    def fields_get(self, allfields=None, attributes=None):
        return super(ApprovalCenter, self).fields_get(allfields=allfields, attributes=attributes)
