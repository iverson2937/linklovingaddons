# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductTemplateW(models.Model):
    _inherit = 'product.template'

    product_img_count = fields.Integer(compute='_compute_product_img_count', string=u'产品照片数量')

    product_img_ids = fields.One2many('ir.attachment', 'product_ir_img_id', u'产品照片')

    def _compute_product_img_count(self):
        for product in self:
            product.product_img_count = len(product.product_img_ids)

    @api.multi
    def action_view_product_img(self):
        action = self.env.ref('base.action_attachment').read()[0]
        action['domain'] = [('product_ir_img_id', 'in', self.ids)]
        # action['domain'] = [('res_id', 'in', self.ids)]
        return action


class ProductIrAttachmentW(models.Model):
    _inherit = 'ir.attachment'

    product_ir_img_id = fields.Many2one('product.template', string=u'产品照片')

    name = fields.Char('Attachment Name', require=False)

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if not (vals.get('res_model') or vals.get('res_id')):
            if self.env.context.get('active_model') == 'product.template':
                if not vals.get('datas'):
                    raise UserError(u"请完善信息")
                vals['product_ir_img_id'] = self.env.context.get('active_ids')[0] if self.env.context.get(
                    'active_ids')  else ''
                # vals['name'] = vals.get('datas_fname')

        return super(ProductIrAttachmentW, self).create(vals)

    @api.onchange('datas')
    def onchange_datas(self):
        for tar in self:
            tar.name = self.datas_fname.split('.')[0] if self.datas_fname else ' '
