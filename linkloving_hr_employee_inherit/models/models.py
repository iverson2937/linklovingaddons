# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

DEFAULT_PASS = '123456'


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        res = super(ResUsers, self).create(vals)
        # 设定初始的密码
        pass_wizard = self.env['change.password.wizard'].create({})

        self.env['change.password.user'].create({
            'wizard_id': pass_wizard.id,
            'user_id': res.id,
            'new_passwd': DEFAULT_PASS
        })
        pass_wizard.change_password_button()
        return res


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    _sql_constraints = [
        ('work_email_key', 'UNIQUE (work_email)', 'email必须唯一!')
    ]

    @api.multi
    def set_user(self):
        user_id = self.env['res.users'].search([('login', '=', self.work_email.strip())])
        if not user_id:
            user_id = self.env['res.users'].create({
                'name': self.name,
                'login': self.work_email,
                'email': self.work_email,
                'groups_id': [
                    (4, self.env.ref('hr.group_hr_user').id),
                ]})

        self.write({
            'address_home_id': user_id.partner_id.id,
            'user_id': user_id.id
        })

    @api.multi
    def set_user_groups(self):
        view_id = self.env.ref('base.view_users_form')
        return {
            'name': '用户',
            'res_model': 'res.users',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view_id.id, 'form')],
            'res_id': self.user_id.id

        }
