# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError


class MrpBomLine(models.Model):
    """
    权限控制
    """
    _inherit = 'mrp.bom.line'

    @api.multi
    def write(self, vals):
        if not self.env.user.has_group('linkloving_warehouse.group_document_control_user'):
            raise UserError('你没有权限修改BOM')
        return super(MrpBomLine, self).write(vals)

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('linkloving_warehouse.group_document_control_user'):
            raise UserError('你没有权限修改BOM')
        return super(MrpBomLine, self).create(vals)

    @api.multi
    def unlink(self):
        if not self.env.user.has_group('linkloving_warehouse.group_document_control_user'):
            raise UserError('你没有权限修改BOM')
        return super(MrpBomLine, self).unlink()
