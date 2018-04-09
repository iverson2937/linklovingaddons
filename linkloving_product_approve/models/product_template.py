# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'ir.needaction_mixin']

    approval_record_ids = fields.One2many('mrp.approval.record', 'product_id')
    flow_jason = fields.Char(compute='get_flow_state')

    @api.multi
    def get_flow_state(self):
        for template in self:
            template.flow_json = {}

    stage_id = fields.Many2one(
        'mrp.approve.stage', 'Stage', copy=False, group_expand='_read_group_stage_ids'
    )

    state = fields.Selection([
        ('draft', u'草稿'),
        ('progress', u'审核中'),
        ('done', u'正式'),
    ], default='draft')
    user_can_approve = fields.Boolean(
        'Can Approve', compute='_compute_user_can_approve',
        help='Technical field to check if approval by current user is required')
    user_can_reject = fields.Boolean(
        'Can Reject', compute='_compute_user_can_reject',
        help='Technical field to check if reject by current user is possible')

    required_user_ids = fields.Many2many('res.users', 'product_template_require_user_rel', 'product_id', 'user_id')
    approved_user_ids = fields.Many2many('res.users', 'product_template_approved_user_rel', 'product_id', 'user_id',
                                         string=u'已审核用户')

    @api.multi
    def _compute_user_can_approve(self):
        for p in self:
            if self.env.user in p.required_user_ids:
                p.user_can_reject = True

    @api.multi
    def _compute_user_can_reject(self):
        for p in self:
            if self.env.user in p.required_user_ids:
                p.user_can_approve = True

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages of the ECO type
        in the Kanban view, even if there is no ECO in that stage
        """
        search_domain = []
        type_id = self.env['mrp.approve.type'].search([('approve_type', '=', 'product')], limited=1)
        if type_id:
            search_domain = [('type_id', '=', type_id.id)]

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.multi
    def submit(self):
        for product in self:
            product.state = 'progress'
            # 提交修改stage 添加待审核人
            type_id = self.env['mrp.approve.type'].search([('approve_type', '=', 'product')], limit=1)
            if type_id:
                stage_id = self.env['mrp.approve.stage'].search([('type_id', '=', type_id.id)])[0]

            product.stage_id = stage_id.id
            product.required_user_ids = [(6, 0, stage_id.required_user_ids.ids)]

    @api.multi
    def approve(self, remark):
        for product in self:
            for app in product.stage_id.approval_template_ids:
                if self.env.user in app.user_ids:
                    self.env['mrp.approval.record'].create({
                        'product_id': product.id,
                        'stage_id': product.stage_id.id,
                        'approval_template_id': app.id,
                        'status': 'approved',
                        'remark': remark,
                        'user_id': self.env.uid
                    })
                    # 审核过待审核中取消

                    product.required_user_ids = [(3, user_id.id) for user_id in app.user_ids]
                    product.approved_user_ids = [(4, self.env.user.id)]

            change_to_next = True
            # 如果阶段所需要的审核都通过了就到下一个阶段
            if product.approval_record_ids:
                for template_id in product.stage_id.approval_template_ids:
                    approvals = product.approval_record_ids.filtered(
                        lambda x: x.approval_template_id == template_id and x.active)
                    #
                    if not approvals:
                        change_to_next = False
                        break
            if change_to_next and product.stage_id.next_stage_id:
                product.stage_id = product.stage_id.next_stage_id.id
                product.required_user_ids = [(6, 0, product.stage_id.required_user_ids.ids)]

            elif product.stage_id.allow_apply_change and change_to_next:
                product.state = 'done'
                product.stage_id = False
            elif not product.stage_id.allow_apply_change and not product.stage_id.next_stage_id:
                raise UserError('请联系管理员设置')

    @api.multi
    def reject(self, remark):
        for product in self:
            for app in product.stage_id.approval_template_ids:
                if self.env.user in app.user_ids:
                    self.env['mrp.approval.record'].create({
                        'product_id': product.id,
                        'stage_id': product.stage_id.id,
                        'approval_template_id': app.id,
                        'status': 'rejected',
                        'remark': remark,
                        'user_id': self.env.uid
                    })

            for r in product.approval_record_ids:
                r.active = False

            if product.stage_id.pre_stage_id:
                product.stage_id = product.stage_id.pre_stage_id.id
            else:
                product.stage_id = False
                product.state = 'draft'
            product.required_user_ids = (5)
            product.approved_user_ids = [(4, self.env.user.id)]

    def to_approve(self):

        context = {'default_reject': self._context.get('default_reject')}
        return {
            'name': u'审核通过',
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': False,
            'res_model': 'product.state.confirm.wizard',
            'domain': [],
            'context': dict(context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # @api.multi
    # def _create_approvals(self):
    #     for product in self:
    #         for approval_template in product.stage_id.approval_template_ids:
    #             self.env['mrp.approval.record'].create({
    #                 'product_id': product.id,
    #                 'approval_template_id': approval_template.id,
    #             })
    #
    # @api.model
    # def create(self, vals):
    #     product = super(ProductTemplate, self).create(vals)
    #     product._create_approvals()
    #     return product
    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        if self._context.get('to_approve'):
            return [('required_user_ids', 'child_of', self.env.user.id)]
