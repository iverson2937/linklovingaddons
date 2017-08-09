# -*- coding: utf-8 -*-
from odoo import http


class LinklovingCrm(http.Controller):
    @http.route('/linkloving_crm/init_partner/', auth='public')
    def init_partner(self, **kw):
        ssr = http.request.env['res.partner']
        ssr.init_public_partner_crm()

        return "init partner succeed"
