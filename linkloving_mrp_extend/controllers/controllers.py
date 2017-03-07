# -*- coding: utf-8 -*-
import json
from urllib2 import URLError

import odoorpc

from odoo import http
from odoo.exceptions import UserError


class LinklovingMrpExtend(http.Controller):
    @http.route('/linkloving_mrp_extend/linkloving_mrp_extend/', auth='none')
    def index(self, **kw):
        url = kw['url']
        port = kw['port']
        try:
            odoo = odoorpc.ODOO(url, port=port)
        except URLError,e:
            return 'error'
        return json.dumps(odoo.db.list())

    @http.route('/linkloving_mrp_extend/linkloving_mrp_extend/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('linkloving_mrp_extend.listing', {
            'root': '/linkloving_mrp_extend/linkloving_mrp_extend',
            'objects': http.request.env['mrp.production'].search([]),
        })

    @http.route('/linkloving_mrp_extend/linkloving_mrp_extend/objects/<model("linkloving_mrp_extend.linkloving_mrp_extend"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('linkloving_mrp_extend.object', {
            'object': obj
        })