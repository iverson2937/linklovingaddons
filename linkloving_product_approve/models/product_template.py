# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    approval_record_ids = fields.One2many('mrp.approval.record', 'product_id')
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

    require_user_ids = fields.Many2many('res.users', compute='_compute_require_user_ids')

    @api.multi
    def _compute_require_user_ids(self):
        for p in self:
            pass

    @api.multi
    def _compute_user_can_approve(self):
        for p in self:
            p.user_can_approve = True

    @api.multi
    def _compute_user_can_reject(self):
        for p in self:
            p.user_can_reject = True

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
            type_id = self.env['mrp.approve.type'].search([('approve_type', '=', 'product')], limit=1)
            if type_id:
                stage_id = self.env['mrp.approve.stage'].search([('type_id', '=', type_id.id)])[0]

            product.stage_id = stage_id.id

    @api.multi
    def approve(self):
        for product in self:
            for app in product.stage_id.approval_template_ids:
                if self.env.user in app.user_ids:
                    self.env['mrp.approval.record'].create({
                        'product_id': product.id,
                        'stage_id': product.stage_id.id,
                        'approval_template_id': app.id,
                        'status': 'approved',
                        'user_id': self.env.uid
                    })
            change_to_next = True
                # 如果阶段所需要的审核都通过了就到下一个阶段
            if product.approval_record_ids:
                for template_id in product.stage_id.approve_template_ids:
                    approvals = product.approval_record_ids.filtered(
                        lambda x: x.approve_template_id == template_id and x.active)
                    if not approvals or approvals.state != 'approved':
                        change_to_next = False
                        break
            if change_to_next and product.stage_id.next_stage_id:
                product.stage_id = product.stage_id.next_stage_id.id

    @api.multi
    def reject(self):
        for product in self:
            for app in product.stage_id.approval_template_ids:
                if self.env.user in app.user_ids:
                    self.env['mrp.approval.record'].create({
                        'product_id': product.id,
                        'stage_id': product.stage_id.id,
                        'approval_template_id': app.id,
                        'status': 'rejected',
                        'user_id': self.env.uid
                    })

            for r in product.approval_record_ids:
                r.active = False

            if product.stage_id.pre_stage_id:
                product.stage_id = product.stage_id.pre_stage_id.id
            else:
                product.stage_id = False
                product.state = 'draft'

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
