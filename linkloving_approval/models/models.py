# -*- coding: utf-8 -*-


ATTACHINFO_FIELD = ['product_tmpl_id', 'file_name', 'review_id', 'remote_path',
                    'version', 'state', 'has_right_to_review', 'is_show_outage',
                    'is_able_to_use', 'is_show_cancel', 'is_first_review',
                    'create_uid', 'type', 'is_delect_view', 'is_show_action_deny', 'create_date', 'remark',
                    'tag_upload_file', 'tag_type_flow_id', 'file_is_update']

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
        is_project_search_type = True if str(domain_my).find("'type") == -1 else False
        domain_my += [('product_tmpl_id', '!=', None)]

        product_view_new = kwargs.get('product_view_new')

        if product_view_new:
            domain = [("product_tmpl_id", '=', product_view_new)]
            attatchments = self.env[self.res_model].search_read(domain + domain_my,
                                                                       limit=limit,
                                                                       offset=offset,
                                                                       order='create_date desc',
                                                                       fields=ATTACHINFO_FIELD)
        else:

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

                lines = self.env["review.process.line"].search(
                    [("state", 'not in', ['waiting_review', 'review_canceled']),
                     ('partner_id', '=', self.env.user.partner_id.id),
                     ('review_order_seq', '!=', 1)],
                    order='write_date desc')
                review_ids = lines.mapped("review_id")
                domain = [("review_id", "in", review_ids.ids)]
                attatchments = self.env[self.res_model].search_read(expression.AND([domain, domain_my]),
                                                                    order='write_date desc',
                                                                    limit=limit,
                                                                    offset=offset,
                                                                    fields=ATTACHINFO_FIELD)

        attach_list = []
        for atta in attatchments:

            temp_show=False
            if self.env.ref('linkloving_approval.group_start_stop_show').id in self.env.user.groups_id.ids:
                temp_show=True
            attach_list.append(
                dict(self.env['product.attachment.info'].convert_attachment_info(atta),
                     **{'checkbox_type': self.type, 'create_date': atta.get('create_date'),
                        'tag_flow_id': atta.get('tag_type_flow_id')[0] if atta.get('tag_type_flow_id') else '',
                        'tag_is_remote_path': 'TRUE' if atta.get('remote_path') else 'FALSE',
                        'is_product_view': False if product_view_new else True, 'temp_is_show_stop_start':temp_show}))

        length = self.env[self.res_model].search_count(expression.AND([domain, domain_my]))

        tag_info_list = []

        for tag_info_one in self.env['tag.info'].search([]):
            domain_tag = []

            if product_view_new:
                tag_num = len(
                    self.env['product.attachment.info'].search(
                        [("type", "=", tag_info_one.name.lower())] + domain))
            else:
                if self.type == 'waiting_submit':
                    domain_tag = [('create_uid', '=', self.env.user.id),
                                  ('state', 'in', ['waiting_release', 'cancel', 'deny'])]
                elif self.type == 'submitted':
                    domain_tag = [('create_uid', '=', self.env.user.id),
                                  ('state', 'not in', ['waiting_release', 'draft', 'cancel', 'deny'])]
                elif self.type == 'waiting_approval':

                    lines = self.env["review.process.line"].search([("state", '=', 'waiting_review'),
                                                                    ('partner_id', '=', self.env.user.partner_id.id)],
                                                                   order='create_date desc')
                    review_ids = lines.mapped("review_id")
                    domain_tag = [("review_id", "in", review_ids.ids),
                                  ('state', 'in', ['review_ing'])]
                    # domain_tag = [("state", '=', 'waiting_review'), ('partner_id', '=', self.env.user.partner_id.id)]
                elif self.type == 'approval':

                    lines = self.env["review.process.line"].search(
                        [("state", 'not in', ['waiting_review', 'review_canceled']),
                         ('partner_id', '=', self.env.user.partner_id.id),
                         ('review_order_seq', '!=', 1)],
                        order='create_date desc')
                    review_ids = lines.mapped("review_id")
                    domain_tag = [("review_id", "in", review_ids.ids)]
                    # domain_tag = [("state", 'not in', ['waiting_review', 'review_canceled']),
                    #               ('partner_id', '=', self.env.user.partner_id.id), ('review_order_seq', '!=', 1)]

                if is_project_search_type:
                    num_domain = domain_tag + domain_my
                else:
                    num_domain = domain_tag

                tag_num = len(self.env['product.attachment.info'].search(
                    expression.AND([[("type", "=", tag_info_one.name.lower())], num_domain])))

            tag_info_list.append({'tag_name': tag_info_one.name, 'tag_num': tag_num,
                                  'view_tag_style': 'view_text_style_down' if tag_num == 0 else 'view_text_style_now',
                                  'product_ax': product_view_new[0] if product_view_new else ''})

        return {"records": attach_list,
                "length": length,
                "tag_type_lists": tag_info_list
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
        result = super(ApprovalCenter, self).fields_get(allfields=allfields, attributes=attributes)

        tag_info_list = []

        for tag_info_one in self.env['tag.info'].search([]):
            tag_num = len(self.env['product.attachment.info'].search(
                [("tag_type_id", "=", tag_info_one.name), ('create_uid', '=', self.env.user.id),
                 ('state', 'in', ['waiting_release', 'cancel', 'deny'])]))

            tag_info_list.append({'tag_name': tag_info_one.name, 'tag_num': tag_num})

        # tag_info_list1 = [tag_info_one.name for tag_info_one in self.env['tag.info'].search([])]

        return dict(result, **{'asdd': tag_info_list})
