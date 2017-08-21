# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class linkloving_app_menu_control(models.Model):
#     _name = 'linkloving_app_menu_control.linkloving_app_menu_control'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
from odoo import tools


class IrMenuExtend(models.Model):
    _inherit = 'ir.ui.menu'

    is_show_on_app = fields.Boolean("Show On App Or Not", default=False, help=u"是否在app中显示该菜单")
    app_menu_icon = fields.Binary("App Menu Icon")
    tip_text = fields.Char(string=u'提示信息')

    @api.onchange('is_show_on_app')
    def onchange_is_show_on_app(self):
        if self.is_show_on_app:
            parent = self.parent_id
            while parent:
                parent.write({'is_show_on_app':True})
                parent = parent.parent_id

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        fields.append("tip_text")
        return super(IrMenuExtend, self).read(fields, load)

class MultiMenu(models.TransientModel):
    _name = 'multi.handle.menu'

    @api.multi
    def action_handle_menu(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        menus = self.env['ir.ui.menu'].search([('id', 'in', active_ids)])
        for menu in menus:
            menu.is_show_on_app = True
            parent = menu.parent_id
            while parent:
                parent.write({'is_show_on_app': True})
                parent = parent.parent_id

