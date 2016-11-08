# -*- coding: utf-8 -*-

# class LinklovingSale(http.Controller):
#     @http.route('/linkloving_sale/linkloving_sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/linkloving_sale/linkloving_sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('linkloving_sale.listing', {
#             'root': '/linkloving_sale/linkloving_sale',
#             'objects': http.request.env['linkloving_sale.linkloving_sale'].search([]),
#         })

#     @http.route('/linkloving_sale/linkloving_sale/objects/<model("linkloving_sale.linkloving_sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('linkloving_sale.object', {
#             'object': obj
#         })