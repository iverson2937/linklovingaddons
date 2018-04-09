# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class LinklovingEmployee(http.Controller):
    @http.route('/linkloving_employee/init_is_create_account', auth='public')
    def index(self, **kw):
        empl_list = request.env['hr.employee'].sudo().search([])
        for empl_one in empl_list:
            empl_one.write({'is_create_account': False})

        return "是否创建用户字段设置为空"

        # @http.route('/linkloving_employee/linkloving_employee/objects/', auth='public')
        # def list(self, **kw):
        #     return http.request.render('linkloving_employee.listing', {
        #         'root': '/linkloving_employee/linkloving_employee',
        #         'objects': http.request.env['linkloving_employee.linkloving_employee'].search([]),
        #     })
        #
        # @http.route('/linkloving_employee/linkloving_employee/objects/<model("linkloving_employee.linkloving_employee"):obj>/', auth='public')
        # def object(self, obj, **kw):
        #     return http.request.render('linkloving_employee.object', {
        #         'object': obj
        #     })
