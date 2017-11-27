# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class LinklovingCrm(http.Controller):
    @http.route('/linkloving_crm/init_partner/', auth='public')
    def init_partner(self, **kw):
        ssr = http.request.env['res.partner']
        ssr.init_public_partner_crm()

        return "init partner succeed"

    @http.route('/linkloving_crm/create_attachment', type='json', auth='public', website=True, csrf=False)
    def create_attachment_index(self, **kw):
        Model_Attachment = request.env['ir.attachment']

        content = kw.get('content')
        file_name = kw.get('file')

        attachment_one = Model_Attachment.create({
            'res_model': u'blog.post',
            'name': file_name,
            'datas': content.split('base64,')[1] if content.split('base64,') else content,
            'datas_fname': file_name,
            'public': True,
        })
        return str(attachment_one.id)
