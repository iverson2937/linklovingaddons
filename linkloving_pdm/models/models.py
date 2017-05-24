# -*- coding: utf-8 -*-

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

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def document_load(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'document_manage',
            'product_id': self.id
        }

class ReviewProcess(models.Model):
    _name = 'review.process'

    @api.multi
    def _compute_who_review_now(self):
        for process in self:
            waiting_review_line = process.review_line_ids.filtered(lambda x: x.state == 'waiting_review')
            if waiting_review_line:
                process.who_review_now =  waiting_review_line[0].partner_id
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

    who_review_now = fields.Many2one("res.partner",string=u'待...审核', compute="_compute_who_review_now")
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
            review_id = self.env["review.process"].create({
                'res_model': res_model,
                'res_id': res_id,
            })
            self.env["review.process.line"].create({
                'partner_id': self.env.user.partner_id.id,
                'review_id': review_id.id,
            })
            return review_id.id


class ReviewProcessLine(models.Model):
    _name = 'review.process.line'

    partner_id = fields.Many2one("res.partner", domain=[('employee','=',True)])
    review_time = fields.Datetime(string=u"操作时间", required=False, )
    state = fields.Selection(string=u"状态", selection=[('waiting_review', u'等待审核'),
                                                      ('review_success', u'审核通过'),
                                                      ('review_fail', u'审核不通过')], required=False,
                             default='waiting_review')

    last_review_line_id = fields.Many2one("review.process.line", string=u"上一次审核")
    review_id = fields.Many2one('review.process')

    is_last_review= fields.Boolean(default=False)

    remark = fields.Text(u"备注")

    def submit_to_next_reviewer(self, to_last_review=False, partner_id=None, remark=None):
        if not partner_id:
            raise UserError(u"请选择审核人!")
        if not self.env["final.review.partner"].get_final_review_partner_id():
            raise UserError(u'请联系管理员,设置终审人!')
        is_last_review = False
        if to_last_review \
                or partner_id.id == self.env["final.review.partner"].get_final_review_partner_id().id:
            is_last_review = True

        #新建一个 审核条目 指向下一个审核人员
        self.env["review.process.line"].create({
            'partner_id': partner_id.id,
            'review_id': self.review_id.id,
            'last_review_line_id': self.id,
            'is_last_review':is_last_review,
        })
        #设置现有的这个审核条目状态等
        self.write({
            'review_time': fields.datetime.now(),
            'state': 'review_success',
            'remark': remark
        })

    # 审核通过
    def action_pass(self):
        pass

    #拒绝审核
    def action_deny(self):
        pass

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

    def _default_version(self):
        model = self._context.get("model")
        res_id = self._context.get("product_id")
        self.env["product.attachment.info"].search([('product_tmpl_id', '=', res_id),
                                                    ])
        return None

    @api.multi
    def _compute_has_right_to_review(self):
        for info in self:
            if info.review_id.who_review_now.user_id == self.env.user.id:
                info.has_right_to_review = True

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
    version = fields.Char(string=u"版本号", default=_default_version)

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
                                readonly=True,)

    type = fields.Selection(string="类型", selection=[('sip', 'SIP'),
                                                    ('sop', 'SOP'),
                                                    ('ipqc', 'IPQC')], required=True, )

    @api.model
    def create(self, vals):
        if (vals.get("file_binary") or vals.get("remote_path")):
            vals['state'] = 'waiting_release'
        return super(ProductAttachmentInfo, self).create(vals)

    @api.multi
    def write(self, vals):
        if (vals.get("file_binary") or vals.get("remote_path")):
            vals['state'] = 'waiting_release'
        return super(ProductAttachmentInfo, self).write(vals)


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
        pass


    # 等待发布 -> 被拒
    @api.multi
    def action_deny(self):
        pass


    # 等待发布 -> 取消
    @api.multi
    def action_cancel(self):
        pass


class ProductTemplateExtend(models.Model):
    _inherit = "product.template"

    sip_files = fields.One2many(comodel_name="product.attachment.info",
                                inverse_name="product_tmpl_id",
                                domain=[("type", "=", "sip")],
                                string="SIP",
                                required=False,
                                )

    sop_files = fields.One2many(comodel_name="product.attachment.info",
                                inverse_name="product_tmpl_id",
                                string="SOP",
                                required=False, )

    ipqc_files = fields.One2many(comodel_name="product.attachment.info",
                                 inverse_name="product_tmpl_id",
                                 string="IPQC",
                                 required=False, )


class ReviewProcessWizard(models.TransientModel):
    _name = 'review.process.wizard'

    partner_id = fields.Many2one("res.partner",string=u'提交给...审核', domain=[('employee','=',True)])
    product_attachment_info_id = fields.Many2one("product.attachment.info")
    review_process_line = fields.Many2one("review.process.line")
    remark = fields.Text(u"备注", required=True)
    # 审核通过
    def action_to_next(self):
        to_last_review = self._context.get("to_last_review")#是否送往终审
        if not self.product_attachment_info_id.review_id:  # 如果没审核过
            self.product_attachment_info_id.action_send_to_review()
        self.product_attachment_info_id.review_id.process_line_review_now.submit_to_next_reviewer(
            to_last_review=to_last_review,
                partner_id=self.partner_id,
                remark=self.remark)


class FinalReviewPartner(models.Model):
    _name = 'final.review.partner'

    final_review_partner_id = fields.Many2one(comodel_name="res.partner", string="终审人", required=False,
                                              domain=[('employee','=',True)])

    def get_final_review_partner_id(self):
        final = self.env["final.review.partner"].search([],limit=1)
        if final:
            return final[0].final_review_partner_id
        else:
            return False