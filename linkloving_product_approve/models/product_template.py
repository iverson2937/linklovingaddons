# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    stage_id = fields.Many2one(
        'mrp.approve.stage', 'Stage', copy=False,
        group_expand='_read_group_stage_ids',
        default=lambda self: self.env['mrp.approve.stage'].search(
            [('type_id', '=', self._context.get('default_type_id'))], limit=1))

    state = fields.Selection([
        ('draft', u'草稿'),
        ('done', u'正式'),
    ], default='draft')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages of the ECO type
        in the Kanban view, even if there is no ECO in that stage
        """
        search_domain = []
        if self._context.get('default_type_id'):
            search_domain = [('type_id', '=', self._context['default_type_id'])]

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.multi
    def approve(self):
        for product in self:
            self.env['mrp.approval.record'].create({
                'product_id': product.id,
                # 'approval_template_id': '',
                'status': 'approved',
                'user_id': self.env.uid
            })

    @api.multi
    def reject(self):
        for product in self:
            self.env['mrp.approval.record'].create({
                'product_id': product.id,
                # 'approval_template_id': '',
                'status': 'rejected',
                'user_id': self.env.uid
            })

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
