# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _name = 'product.approve.stage'
    name = fields.Char(string='名称')


class MrpApprovalTemplate(models.Model):
    _name = 'mrp.approval.template'


class MrpApproveStage(models.Model):
    _name = 'mrp.approve.stage'
    _description = 'Engineering Change Order Stage'
    _order = "sequence, id"
    _fold_name = 'folded'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=0)
    # folded = fields.Boolean('Folded in kanban view')
    # allow_apply_change = fields.Boolean('Final Stage')
    # type_id = fields.Many2one('mrp.eco.type', 'Type', required=True, default=lambda self: self.env['mrp.eco.type'].search([], limit=1))
    approval_template_ids = fields.One2many('mrp.approval.template', 'stage_id', 'Approvals')

    # approval_roles = fields.Char('Approval Roles', compute='_compute_approvals', store=True)
    # is_blocking = fields.Boolean('Blocking Stage', compute='_compute_is_blocking', store=True)

    @api.one
    @api.depends('approval_template_ids.name')
    def _compute_approvals(self):
        self.approval_roles = ', '.join(self.approval_template_ids.mapped('name'))

    @api.one
    @api.depends('approval_template_ids.approval_type')
    def _compute_is_blocking(self):
        self.is_blocking = any(template.approval_type == 'mandatory' for template in self.approval_template_ids)
