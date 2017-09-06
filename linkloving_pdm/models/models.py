# -*- coding: utf-8 -*-
import os

from odoo import models, fields, api

# class linkloving_pdm(models.Model):
#     _name = 'linkloving_pdm.linkloving_pdm'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
from odoo.exceptions import UserError

REVIEW_LINE_STATE = {'waiting_review': u'等待审核',
                     'review_success': u'审核通过',
                     'review_fail': u'审核不通过',
                     'review_canceled': u'取消审核'}


class ReviewProcess(models.Model):
    _name = 'review.process'

    @api.multi
    @api.depends("review_line_ids")
    def _compute_who_review_now(self):
        for process in self:
            waiting_review_line = process.review_line_ids.filtered(lambda x: x.state == 'waiting_review')
            if waiting_review_line:
                process.who_review_now = waiting_review_line[0].partner_id
            else:
                process.who_review_now = None

    @api.multi
    def _compute_process_line_review_now(self):
        for process in self:
            waiting_review_line = process.review_line_ids.filtered(lambda x: x.state == 'waiting_review')
            if waiting_review_line:
                process.process_line_review_now = waiting_review_line[0]
            else:
                process.process_line_review_now = None

    res_model = fields.Char('Related Model', required=True, index=True, help='Model of the followed resource')
    res_id = fields.Integer('Related ID', index=True, help='Id of the followed resource')
    review_line_ids = fields.One2many("review.process.line", "review_id", string=u"审核过程")

    who_review_now = fields.Many2one("res.partner", string=u'待...审核', compute="_compute_who_review_now", store=True)
    process_line_review_now = fields.Many2one("review.process.line", compute="_compute_process_line_review_now")

    @api.multi
    def name_get(self):
        res = []
        for process in self:
            if process.who_review_now:
                res.append((process.id, process.who_review_now.name))
            else:
                res.append((process.id, u'已审核完毕'))
        return res

    # 开启一次审核流程
    def create_review_process(self, res_model, res_id):
        line = self.env["review.process.line"].create({
            'partner_id': self.env.user.partner_id.id,
            'review_order_seq': 1,
        })
        review_id = self.env["review.process"].create({
            'res_model': res_model,
            'res_id': res_id,
        })
        line.review_id = review_id.id
        return review_id.id

    # 获得审核全流程
    def get_review_line_list(self):
        sorted_line = sorted(self.review_line_ids, key=lambda x: x.review_order_seq)
        line_list = []
        for line in sorted_line:
            line_list.append({
                'id': line.id,
                'name': line.partner_id.name,
                'remark': line.remark or '',
                'state': [line.state, REVIEW_LINE_STATE[line.state]],
                'create_date': line.create_date,
            })
        return line_list


class ReviewProcessLine(models.Model):
    _name = 'review.process.line'

    partner_id = fields.Many2one("res.partner", domain=[('employee', '=', True)])
    review_time = fields.Datetime(string=u"操作时间", required=False, )
    state = fields.Selection(string=u"状态", selection=[('waiting_review', u'等待审核'),
                                                      ('review_success', u'审核通过'),
                                                      ('review_fail', u'审核不通过'),
                                                      ('review_canceled', u'取消审核')], required=False,
                             default='waiting_review')

    last_review_line_id = fields.Many2one("review.process.line", string=u"上一次审核")
    review_id = fields.Many2one('review.process')

    is_last_review = fields.Boolean(default=False)

    review_order_seq = fields.Integer(string=u'审核顺序', help=u"从1开始")  # 从1开始
    remark = fields.Text(u"备注")

    def submit_to_next_reviewer(self, review_type, to_last_review=False, partner_id=None, remark=None):

        if not partner_id:
            raise UserError(u"请选择审核人!")

        if to_last_review:
            if not self.env['final.review.partner'].search([('final_review_partner_id', '=', partner_id.id),
                                                            ('review_type', '=', review_type)]):
                raise UserError('请选择终正确的终审人')

        is_last_review = False
        if to_last_review \
                or partner_id.id == self.env["final.review.partner"].get_final_review_partner_id(review_type).id:
            is_last_review = True

        # 设置现有的这个审核条目状态等
        self.write({
            'review_time': fields.datetime.now(),
            'state': 'review_success',
            'remark': remark
        })

        # 新建一个 审核条目 指向下一个审核人员
        self.env["review.process.line"].create({
            'partner_id': partner_id.id,
            'review_id': self.review_id.id,
            'last_review_line_id': self.id,
            'review_order_seq': self.review_order_seq + 1,
            'is_last_review': is_last_review,
        })

    # 审核通过
    def action_pass(self, remark):
        review_type = self._context.get('review_type')

        if self.env["final.review.partner"].get_final_review_partner_id(review_type).id == self.env.user.partner_id.id:
            self.write({
                'review_time': fields.datetime.now(),
                'state': 'review_success',
                'remark': remark
            })

        else:
            raise UserError(u"终审人才能进行审核")

    def action_approve(self, remark):
        if self.review_id.who_review_now.id == self.env.user.partner_id.id:
            self.write({
                'review_time': fields.datetime.now(),
                'state': 'review_success',
                'remark': remark
            })

        else:
            raise UserError(u"您不是审核人")

    # 拒绝审核
    def action_deny(self, remark):
        self.write({
            'review_time': fields.datetime.now(),
            'state': 'review_fail',
            'remark': remark
        })
        # 新建一个 审核条目 指向最初的人
        self.env["review.process.line"].create({
            'partner_id': self.review_id.create_uid.partner_id.id,
            'review_id': self.review_id.id,
            'last_review_line_id': self.id,
            'review_order_seq': self.review_order_seq + 1,
        })

    def action_cancel(self, remark):
        self.write({
            'review_time': fields.datetime.now(),
            'state': 'review_canceled',
            'remark': remark
        })
        # 新建一个 审核条目 指向最初的人
        self.env["review.process.line"].create({
            'partner_id': self.review_id.create_uid.partner_id.id,
            'review_id': self.review_id.id,
            'last_review_line_id': self.id,
            'review_order_seq': self.review_order_seq + 1,
        })


FILE_TYPE = [('sip', 'SIP'),
             ('sop', 'SOP'),
             ('ipqc', 'IPQC'),
             ('project', u'工程'),
             ('other', 'Other'),
             ('design', 'Design')]
FILE_TYPE_DIC = {'sip': 'SIP',
                 'sop': 'SOP',
                 'ipqc': 'IPQC',
                 'project': u'工程',
                 'other': 'Other',
                 'design': 'Design'}


class ProductAttachmentInfo(models.Model):
    _name = 'product.attachment.info'

    # def _default_product_id(self):
    #     model = self._context.get("model")
    #     res_id = self._context.get("product_id")
    #     if model == 'product.template':
    #         product_tmpl = self.env[model].browse(res_id)
    #         if product_tmpl.product_variant_ids:
    #             return product_tmpl.product_variant_ids[0].id
    #         else:
    #             return res_id

    def convert_attachment_info(self):
        return {
            'product_id': {
                'id': self.product_tmpl_id.id,
                'name': self.product_tmpl_id.display_name,
                'default_code': self.product_tmpl_id.default_code,
            },
            'id': self.id,
            'file_name': self.file_name or '',
            'review_id': self.review_id.who_review_now.name or '',
            'remote_path': self.remote_path or '',
            'version': self.version or '',
            'state': [self.state, ATTACHMENT_STATE[self.state]],
            'has_right_to_review': self.has_right_to_review,
            'review_line': self.review_id.get_review_line_list(),
            'is_able_to_use': self.is_able_to_use,
            'is_show_cancel': self.is_show_cancel,
            'is_first_review': self.is_first_review,
            'is_show_action_deny': self.is_show_action_deny,
            'create_uid_name': self.create_uid.name,
            'type': FILE_TYPE_DIC.get(self.type or '') or '',
        }

    def get_file_download_url(self, type, host, product_tmpl_id):
        files = self.search([('product_tmpl_id', '=', product_tmpl_id), ('type', '=', type)])
        file = files.filtered(lambda x: x.is_able_to_use)
        if len(file) == 1:
            return host + 'download_file/?download=true&id=' + str(file[0].id)
        elif len(file) == 0:
            return ''
        else:
            raise u"数据异常,有两个可用的文件"

    def get_download_filename(self):
        dc = self.product_tmpl_id.default_code  # .replace(".", "_")
        file_ext = self.file_name.split('.')[-1:][0]
        if file_ext:
            file_ext = '.' + file_ext
        else:
            file_ext = ''
        if self.state != 'released':
            return 'Unrelease_' + self.type.upper() + '_' + dc + '_v' + str(self.version) + file_ext
        return self.type.upper() + '_' + dc + '_v' + str(self.version) + file_ext

    def default_version(self):
        return self._default_version()

    def _default_version(self):
        model = self._context.get("model")
        res_id = self._context.get("product_id")
        type = self._context.get("type")
        if not res_id or not type:
            raise UserError(u"找不到对应的文件类型或产品")
        attachs = self.env["product.attachment.info"].search([('product_tmpl_id', '=', res_id),
                                                              ('type', '=', type)])
        return max(attachs.mapped("version")) + 1 if attachs.mapped("version") else 1

    @api.multi
    def _compute_is_able_to_use(self):
        for info in self:
            attachs = self.env["product.attachment.info"].search([('product_tmpl_id', '=', info.product_tmpl_id.id),
                                                                  ('type', '=', info.type)])
            if attachs.mapped("version"):
                if info.version == max(attachs.mapped("version")) and info.state == 'released':
                    info.is_able_to_use = True

    @api.multi
    def _compute_has_right_to_review(self):
        for info in self:
            if self.env.user.id in info.review_id.who_review_now.user_ids.ids and info.state in ['review_ing']:
                info.has_right_to_review = True

    @api.multi
    def _compute_is_show_cancel(self):
        for info in self:
            if self.env.user.id == info.create_uid.id and info.state == 'review_ing':
                info.is_show_cancel = True

    @api.multi
    def _compute_is_first_review(self):
        for info in self:
            if self.env.user.id == info.create_uid.id and info.state in ['draft', 'waiting_release', 'deny', 'cancel']:
                info.is_first_review = True

    @api.multi
    def _compute_is_show_action_deny(self):
        for info in self:
            if info.create_uid.id == self.env.user.id and info.state in ['waiting_release', 'cancel', 'deny']:
                info.is_show_action_deny = False
            else:
                info.is_show_action_deny = True

    is_first_review = fields.Boolean(compute='_compute_is_first_review')
    is_show_cancel = fields.Boolean(compute='_compute_is_show_cancel')
    file_name = fields.Char(u"文件名")
    remote_path = fields.Char(string=u"远程路径", required=False, )
    file_binary = fields.Binary()
    state = fields.Selection(string=u"状态", selection=[('draft', u'等待文件'),
                                                      ('waiting_release', u'等待发布'),
                                                      ('review_ing', u'审核中'),
                                                      ('released', u'已发布'),
                                                      ('deny', u'被拒'),
                                                      ('cancel', u'已取消')],
                             default='draft', required=False, readonly=True)
    version = fields.Integer(string=u"版本号", default=_default_version)

    is_able_to_use = fields.Boolean(string=u"是否可以使用", compute="_compute_is_able_to_use")
    has_right_to_review = fields.Boolean(compute='_compute_has_right_to_review')
    # product_id = fields.Many2one(
    #         'product.product', 'Product',default='_default_product_id',
    #         readonly=True)

    product_tmpl_id = fields.Many2one('product.template',
                                      string=u"产品",
                                      # related='product_id.product_tmpl_id',
                                      readonly=True)  # 该产品

    review_id = fields.Many2one("review.process",
                                string=u'待...审核',
                                track_visibility='always',
                                readonly=True, )

    type = fields.Selection(string="类型", selection=FILE_TYPE, required=True, )
    is_show_action_deny = fields.Boolean(string=u'是否显示审核不通过', default=True, compute='_compute_is_show_action_deny')

    @api.model
    def create(self, vals):
        if (vals.get("file_binary") or vals.get("remote_path")):
            vals['state'] = 'waiting_release'
        res = super(ProductAttachmentInfo, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if (vals.get("file_binary") or vals.get("remote_path")):
            vals['state'] = 'waiting_release'
        return super(ProductAttachmentInfo, self).write(vals)

    @api.one
    def update_attachment(self, **kwargs):
        update_dic = {}
        if kwargs.get("file_binary"):
            update_dic["file_binary"] = kwargs.get("file_binary")
        if kwargs.get("file_name"):
            update_dic["file_name"] = kwargs.get("file_name")
        if kwargs.get("remote_path"):
            update_dic["remote_path"] = kwargs.get("remote_path")
            update_dic["file_name"] = os.path.basename(kwargs.get("remote_path"))
        if self.state not in ['waiting_release', 'draft', 'deny', 'cancel']:
            raise UserError(u'文件正在处于审核中,请先取消审核,再进行操作')
        self.write(update_dic)
        return True

    # @api.multi
    # def _compute_version(self):
    #     for info in self:
    #         info.version = self.env['ir.sequence'].next_by_code('product.attachment.info')

    @api.multi
    def _check_file_or_remote_path(self):
        for info in self:
            if not (info.file_binary or info.remote_path):
                raise UserError(u"该单据还未上传文件不能进行下一步操作")

    # 等待文件 -> 等待发布
    @api.multi
    def action_waiting_release(self):
        self._check_file_or_remote_path()
        self.write({
            'state': 'waiting_release'
        })

    # 等待发布 -> 审核中
    @api.multi
    def action_send_to_review(self):
        self._check_file_or_remote_path()
        if not self.review_id:
            self.review_id = self.env["review.process"].create_review_process('product.attachment.info', self.id)
        self.write({
            'state': 'review_ing',
        })

    # 等待发布 -> 已发布
    @api.multi
    def action_released(self):
        self._check_file_or_remote_path()
        self.write({
            'state': 'released'
        })

    # 等待发布 -> 被拒
    @api.multi
    def action_deny(self):
        for info in self:
            if info.state in ['deny', 'waiting_release']:
                raise UserError(u"该文件不在审核中,无法审核不通过")

        self.write({
            'state': 'deny'
        })

    # 等待发布 -> 取消
    @api.multi
    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })


ATTACHMENT_STATE = {
    'draft': u'等待文件',
    'waiting_release': u'等待提交审核',
    'review_ing': u'审核中',
    'released': u'已发布',
    'deny': u'被拒',
    'cancel': u"已取消",
}


class ProductTemplateExtend(models.Model):
    _inherit = "product.template"

    @api.multi
    def document_load(self):
        return {
            'name': '文件',
            'type': 'ir.actions.client',
            'tag': 'document_manage',
            'product_id': self.id
        }

    #####
    def get_file_type_list(self):
        pinfo = {
            'default_code': self.default_code,
            'product_id': self.id,
        }
        return {'list': [
            {'name': 'SIP',
             'type': 'sip',
             'files': self.convert_attendment_info_list(type='sip'),
             'upload_type': 'sys',
             },
            {'name': 'SOP',
             'type': 'sop',
             'upload_type': 'sys',
             },
            {'name': 'IPQC',
             'type': 'ipqc',
             'upload_type': 'sys',
             },
            {'name': u'工程',
             'type': 'project',
             'upload_type': 'sys',
             },
            {'name': 'OTHER',
             'type': 'other',
             'upload_type': 'ftp',
             },
            {'name': 'DESIGN',
             'type': 'design',
             'upload_type': 'ftp',
             },
        ],
            'info': pinfo}

    def get_attachemnt_info_list(self, **kwargs):
        type = kwargs.get('type')
        if not type:
            type = 'sip'
        return {
            'type': type,
            'files': self.convert_attendment_info_list(type),
        }

    def convert_attendment_info_list(self, type):
        files = self.env["product.attachment.info"].search(
            [("type", "=", type), ("product_tmpl_id", '=', self.id)], order='version desc')
        json_list = []
        for a_file in files:
            json_list.append(a_file.convert_attachment_info())
        return json_list

    # def convert_attachment_info(self, info):
    #     return {
    #         'id': info.id,
    #         'file_name': info.file_name or '',
    #         'review_id': info.review_id.who_review_now.name or '',
    #         'remote_path': info.remote_path or '',
    #         'version': info.version or '',
    #         'state': [info.state, ATTACHMENT_STATE[info.state]],
    #         'has_right_to_review': info.has_right_to_review,
    #         'review_line': info.review_id.get_review_line_list(),
    #         'is_able_to_use': info.is_able_to_use,
    #         'is_show_cancel': info.is_show_cancel,
    #         'is_first_review': info.is_first_review,
    #         'create_uid_name': info.create_uid.name,
    #     }

    #####

    sip_files = fields.One2many(comodel_name="product.attachment.info",
                                inverse_name="product_tmpl_id",
                                domain=[("type", "=", "sip")],
                                string="SIP",
                                required=False,
                                )

    sop_files = fields.One2many(comodel_name="product.attachment.info",
                                inverse_name="product_tmpl_id",
                                domain=[("type", "=", "sop")],
                                string="SOP",
                                required=False, )

    ipqc_files = fields.One2many(comodel_name="product.attachment.info",
                                 inverse_name="product_tmpl_id",
                                 domain=[("type", "=", "ipqc")],
                                 string="IPQC",
                                 required=False, )

    other_files = fields.One2many(comodel_name="product.attachment.info",
                                  inverse_name="product_tmpl_id",
                                  domain=[("type", "=", "other")],
                                  string="Other",
                                  required=False, )
    design_files = fields.One2many(comodel_name="product.attachment.info",
                                   inverse_name="product_tmpl_id",
                                   domain=[("type", "=", "design")],
                                   string="Design",
                                   required=False, )


class ReviewProcessCancelWizard(models.TransientModel):
    _name = 'review.process.cancel.wizard'

    product_attachment_info_id = fields.Many2one("product.attachment.info")
    bom_id = fields.Many2one("mrp.bom")
    review_process_line = fields.Many2one("review.process.line",
                                          related="product_attachment_info_id.review_id.process_line_review_now")

    remark = fields.Text(u"备注", required=True)

    def action_cancel_review(self):
        self.review_process_line.action_cancel(self.remark)
        print self._context, 'dddddddd'
        if self._context.get('review_type') == 'bom_review':

            self.bom_id.action_cancel()
        elif self._context.get('review_type') == 'file_review':
            self.product_attachment_info_id.action_cancel()


class ReviewProcessWizard(models.TransientModel):
    _name = 'review.process.wizard'

    cur_partner_id = fields.Many2one('res.partner', default=lambda self: self.env.user.partner_id)
    partner_id = fields.Many2one("res.partner", string=u'提交给...审核', domain=[('employee', '=', True), ])
    product_attachment_info_id = fields.Many2one("product.attachment.info")
    bom_id = fields.Many2one('mrp.bom')
    # material_request_id = fields.Many2one('material.request')

    @api.model
    def _get_default_need_sop(self):
        files = self.env['product.attachment.info'].search(
            [('product_tmpl_id', '=', self.bom_id.product_tmpl_id.id), ('type', '=', 'sop')])
        if files:
            return 1

    @api.model
    def _get_default_value(self):
        files = self.env['product.attachment.info'].search(
            [('product_tmpl_id', '=', self.bom_id.product_tmpl_id.id), ('type', '=', 'sop')])
        if files:
            sop_name = files[0].file_name
        else:
            sop_name = u'未上传'
        return sop_name

    need_sop = fields.Selection([
        (1, u'需要'),
        (2, u'不需要'),
    ], string=u'是否需要SOP文件', default=_get_default_need_sop)
    sop_name = fields.Char(string=u'SOP文件', default=_get_default_value)
    review_process_line = fields.Many2one("review.process.line",
                                          related="product_attachment_info_id.review_id.process_line_review_now")
    review_bom_line = fields.Many2one("review.process.line",
                                      related="bom_id.review_id.process_line_review_now")

    # material_line = fields.Many2one("review.process.line",
    #                                 related="material_request_id.review_id.process_line_review_now")

    remark = fields.Text(u"备注")
    is_show_action_deny = fields.Boolean(default=True)

    # 送审
    def action_to_next(self):
        to_last_review = self._context.get("to_last_review")  # 是否送往终审
        review_type = self._context.get("review_type")

        materials_request_id = self._context.get('default_material_requests_id')
        picking_state = self._context.get('picking_state', False)

        if review_type == 'bom_review':
            if not self.need_sop:
                raise UserError(u'请选择是否需要SOP文件')
            if not self.bom_id.review_id:  # 如果没审核过
                self.bom_id.action_send_to_review()
            self.bom_id.need_sop = self.need_sop
            self.bom_id.state = 'review_ing'  # 被拒之后 修改状态 wei 审核中
            self.bom_id.review_id.process_line_review_now.submit_to_next_reviewer(
                review_type=review_type,
                to_last_review=to_last_review,
                partner_id=self.partner_id,
                remark=self.remark)

            return True
        elif review_type == 'file_review':
            if not self.product_attachment_info_id.review_id:  # 如果没审核过
                self.product_attachment_info_id.action_send_to_review()

            self.product_attachment_info_id.state = 'review_ing'  # 被拒之后 修改状态 wei 审核中
            self.product_attachment_info_id.review_id.process_line_review_now.submit_to_next_reviewer(
                review_type=review_type,
                to_last_review=to_last_review,
                partner_id=self.partner_id,
                remark=self.remark)
        elif review_type == 'picking_review':
            print self.material_requests_id.review_id
            if not self.material_requests_id.review_id:  # 如果没审核过
                self.material_requests_id.action_send_to_review()

            self.material_requests_id.picking_state = 'review_ing'  # 被拒之后 修改状态 wei 审核中

            material_one = self.env['material.request'].browse(materials_request_id)

            if self.env.uid != material_one.create_uid.id:
                self.material_requests_id.write({'review_i_approvaled_val': [(4, self.env.uid)]})

            self.material_requests_id.review_id.process_line_review_now.submit_to_next_reviewer(
                review_type=review_type,
                to_last_review=to_last_review,
                partner_id=self.partner_id,
                remark=self.remark)

        return True

    # 终审 审核通过
    def action_pass(self):

        review_type = self._context.get("review_type")
        materials_request_id = self._context.get('default_material_requests_id')
        if review_type == 'bom_review':
            if not self.need_sop:
                raise UserError(u'请选择是否需要SOP文件')
            self.bom_id.need_sop = self.need_sop
            self.bom_id.action_released()

            self.review_bom_line.action_pass(self.remark)
            # self.bom_id.product_tmpl_id.apply_bom_update()
        elif review_type == 'file_review':
            self.product_attachment_info_id.action_released()
            # 审核通过

            self.review_process_line.action_pass(self.remark)
        elif review_type == 'picking_review':

            self.material_requests_id.picking_state = 'approved_finish'
            self.material_requests_id.write({'review_i_approvaled_val': [(4, self.env.uid)]})
            # 创建出货单
            material_one = self.env['material.request'].browse(materials_request_id)

            picking_out_material = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'location_dest_id': self.env.ref('linkloving_eb.stock_location_eb_transfer_2').id,
                'material_request_order_id': material_one.id,
                'origin': material_one.name,
                'note': material_one.remark,
                'Materials_development_way': material_one.Materials_development_way,
                'partner_id': material_one.create_uid.partner_id.id,
            })
            for one_line in material_one.line_ids:
                self.env['stock.move'].create({
                    'name': 'another move',
                    'product_id': one_line.product_id.id,
                    'product_uom_qty': one_line.product_qty,
                    'product_uom': one_line.product_id.uom_id.id,
                    'picking_id': picking_out_material.id,
                    'location_id': self.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': self.env.ref('linkloving_eb.stock_location_eb_transfer').id})

            self.material_line.action_pass(self.remark)
        return True

    # 审核不通过
    def action_deny(self):
        # 改变文件状态
        review_type = self._context.get('review_type')
        if review_type == 'bom_review':
            self.bom_id.action_deny()
            self.review_bom_line.action_deny(self.remark)
        elif review_type == 'file_review':
            self.product_attachment_info_id.action_deny()
            self.review_process_line.action_deny(self.remark)
        elif review_type == 'picking_review':
            # 改变状态 即可
            # pick_type = self._context.get('picking_state')
            # if pick_type == 'submitted':
            self.material_requests_id.picking_state = 'Refused'
            # self.material_request_id.write({'review_i_approvaled_val': [(4, self.partner_id.user_ids.id)]})
            self.material_requests_id.write({'review_i_approvaled_val': [(4, self.env.uid)]})

            self.material_line.action_deny(self.remark)

        return True

    def action_cancel_review(self):
        review_type = self._context.get('review_type')
        if review_type == 'bom_review':
            self.bom_id.action_cancel()
            self.review_bom_line.action_cancel(self.remark)
        elif review_type == 'file_review':
            self.product_attachment_info_id.action_cancel()
            self.review_process_line.action_cancel(self.remark)
        elif review_type == 'picking_review':
            self.material_requests_id.picking_state = 'to_submit'
            self.review_process_line.action_cancel(self.remark)

    @api.model
    def create(self, vals):
        # if 'need_sop' in vals:
        #     print vals
        #     self.bom_id.need_sop = vals['need_sop']

        return super(ReviewProcessWizard, self).create(vals)


class FinalReviewPartner(models.Model):
    _name = 'final.review.partner'
    review_type = fields.Selection([
        ('bom_review', u'BOM 终审人'),
        ('file_review', u'文件终审人'),
        ('picking_review', u'领料终审人'),
    ], string=u'审核类型')

    final_review_partner_id = fields.Many2one(comodel_name="res.partner", string="终审人", required=False,
                                              domain=[('employee', '=', True)])

    _sql_constraints = {
        ('review_type_unique', 'unique( review_type)',
         '每个类型的终审人只能有一个')
    }

    def get_final_review_partner_id(self, review_type):
        final = self.env["final.review.partner"].search([('review_type', '=', review_type)], limit=1)
        if final:
            return final[0].final_review_partner_id
        else:
            return False

    @api.model
    def create(self, vals):
        res = super(FinalReviewPartner, self).create(vals)
        users = res.final_review_partner_id.user_ids
        review_type_ref = self.get_review_type_ref(vals.get("review_type"))
        for user in users:
            user.groups_id = [(4, self.env.ref(review_type_ref).id)]
        return res
        # group_final_review_partner

    @api.multi
    def unlink(self):
        user_ids = self.final_review_partner_id.user_ids
        review_type_ref = self.get_review_type_ref(self.review_type)
        for user in user_ids:
            user.groups_id = [(2, self.env.ref(review_type_ref).id)]

        return super(FinalReviewPartner, self).unlink()

    @api.multi
    def write(self, vals):
        if vals.get("review_type"):
            review_type_ref = self.get_review_type_ref(vals.get("review_type"))
        else:
            review_type_ref = self.get_review_type_ref(self.review_type)

        group = self.env.ref(review_type_ref).id
        user_ids = self.final_review_partner_id.user_ids
        for user in user_ids:
            user.groups_id = [(2, group)]

        res = super(FinalReviewPartner, self).write(vals)

        users = self.final_review_partner_id.user_ids
        for user in users:
            user.groups_id = [(4, group)]

        return res

    def get_review_type_ref(self, val):
        if val == 'file_review':
            review_type_ref = 'linkloving_pdm.group_final_review_partner'
        elif val == 'bom_review':
            review_type_ref = 'linkloving_pdm.group_final_review_partner_bom'
        elif val == 'picking_review':
            review_type_ref = 'linkloving_pdm.group_final_review_picking'
        else:
            raise UserError(u"数据异常,未找到对应的审核人类型")

        return review_type_ref
