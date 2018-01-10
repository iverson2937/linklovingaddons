# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpApprovalTemplate(models.Model):
    _name = 'mrp.approval.template'
    approve_type = fields.Selection([
        ('document', '文件'),
        ('purchase', '采购'),
        ('research', '研发'),
        ('engineer', '工程'),
        ('final', '终审')
    ])
    sequence = fields.Integer()
    stage_id = fields.Many2one('mrp.approve.stage')
    user_ids = fields.Many2many('res.users')


class MrpApprovalRecord(models.Model):
    _name = 'mrp.approval.record'

    product_id = fields.Many2one(
        'product.template', 'ECO',
        ondelete='cascade', required=True)
    approval_template_id = fields.Many2one(
        'mrp.approval.template', 'Template',
        ondelete='cascade', required=True)
    # name = fields.Char('Role', related='approval_template_id.name', store=True)
    user_id = fields.Many2one(
        'res.users', 'Approved by')
    required_user_ids = fields.Many2many(
        'res.users', string='Requested Users', related='approval_template_id.user_ids')
    template_stage_id = fields.Many2one(
        'mrp.mrp.stage', 'Approval Stage',
        related='approval_template_id.stage_id', store=True)
    eco_stage_id = fields.Many2one(
        'mrp.eco.stage', 'ECO Stage',
        related='product_id.stage_id', store=True)
    status = fields.Selection([
        ('none', 'Not Yet'),
        ('comment', 'Commented'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')], string='Status',
        default='none', required=True)
    # is_approved = fields.Boolean(
    #     compute='_compute_is_approved', store=True)
    # is_rejected = fields.Boolean(
    #     compute='_compute_is_rejected', store=True)
    #
    # @api.one
    # @api.depends('status', 'approval_template_id.approval_type')
    # def _compute_is_approved(self):
    #     if self.approval_template_id.approval_type == 'mandatory':
    #         self.is_approved = self.status == 'approved'
    #     else:
    #         self.is_approved = True

    # @api.one
    # @api.depends('status', 'approval_template_id.approval_type')
    # def _compute_is_rejected(self):
    #     if self.approval_template_id.approval_type == 'mandatory':
    #         self.is_rejected = self.status == 'rejected'
    #     else:
    #         self.is_rejected = False



class MrpApproveStage(models.Model):
    _name = 'mrp.approve.stage'
    _description = 'Engineering Change Order Stage'
    _order = "sequence, id"
    _fold_name = 'folded'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=0)
    # folded = fields.Boolean('Folded in kanban view')
    allow_apply_change = fields.Boolean('Final Stage')
    # type_id = fields.Many2one('mrp.eco.type', 'Type', required=True, default=lambda self: self.env['mrp.eco.type'].search([], limit=1))
    approval_template_ids = fields.One2many('mrp.approval.template', 'stage_id', 'Approvals')

    # approval_roles = fields.Char('Approval Roles', compute='_compute_approvals', store=True)
    # is_blocking = fields.Boolean('Blocking Stage', compute='_compute_is_blocking', store=True)

    # @api.one
    # @api.depends('approval_template_ids.name')
    # def _compute_approvals(self):
    #     self.approval_roles = ', '.join(self.approval_template_ids.mapped('name'))
    #
    # @api.one
    # @api.depends('approval_template_ids.approval_type')
    # def _compute_is_blocking(self):
    #     self.is_blocking = any(template.approval_type == 'mandatory' for template in self.approval_template_ids)
